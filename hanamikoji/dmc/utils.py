import os
import typing
import logging
import traceback
import numpy as np
from collections import Counter
import time

import torch
from torch import multiprocessing as mp

from hanamikoji.dmc.env_utils import Environment
from hanamikoji.env.env import my_move2array, Env, ROUND_MOVES, MOVE_VECTOR_SIZE, X_NO_MOVE_FEATURE_SIZE

shandle = logging.StreamHandler()
shandle.setFormatter(
    logging.Formatter(
        '[%(levelname)s:%(process)d %(module)s:%(lineno)d %(asctime)s] '
        '%(message)s'))
log = logging.getLogger('hanamikojizero')
log.propagate = False
log.addHandler(shandle)
log.setLevel(logging.INFO)

# Buffers are used to transfer data between actor processes
# and learner processes. They are shared tensors in GPU
Buffers = typing.Dict[str, typing.List[torch.Tensor]]


def my_move2tensor(list_cards):
    matrix = my_move2array(list_cards)
    matrix = torch.from_numpy(matrix)
    return matrix


def create_env(flags):
    return Env(flags.objective)


def get_batch(free_queue,
              full_queue,
              buffers,
              flags,
              lock):
    """
    This function will sample a batch from the buffers based
    on the indices received from the full queue. It will also
    free the indices by sending it to full_queue.
    """
    with lock:
        indices = [full_queue.get() for _ in range(flags.batch_size)]
    batch = {
        key: torch.stack([buffers[key][m] for m in indices], dim=1)
        for key in buffers
    }
    for m in indices:
        free_queue.put(m)
    return batch


def create_optimizers(flags, learner_model):
    """
    Create two optimizers for the two round ids.
    """
    round_ids = ['first', 'second']
    optimizers = {}
    for round_id in round_ids:
        optimizer = torch.optim.RMSprop(
            learner_model.parameters(round_id),
            lr=flags.learning_rate,
            momentum=flags.momentum,
            eps=flags.epsilon,
            alpha=flags.alpha)
        optimizers[round_id] = optimizer
    return optimizers


def create_buffers(flags, device_iterator):
    """
    We create buffers for different player ids as well as
    for different devices (i.e., GPU). That is, each device
    will have two buffers for the two player ids.
    """
    T = flags.unroll_length
    player_ids = ['first', 'second']
    buffers = {}
    for device in device_iterator:
        buffers[device] = {}
        for player_id in player_ids:
            specs = dict(
                done=dict(size=(T,), dtype=torch.bool),
                target=dict(size=(T,), dtype=torch.float32),
                obs_x_no_move=dict(size=(T, X_NO_MOVE_FEATURE_SIZE), dtype=torch.int8),
                obs_move=dict(size=(T, MOVE_VECTOR_SIZE), dtype=torch.int8),
                obs_z=dict(size=(T, ROUND_MOVES, MOVE_VECTOR_SIZE), dtype=torch.int8),
            )
            _buffers: Buffers = {key: [] for key in specs}
            for _ in range(flags.num_buffers):
                for key in _buffers:
                    if not device == "cpu":
                        _buffer = torch.empty(**specs[key]).to(torch.device('cuda:' + str(device))).share_memory_()
                    else:
                        _buffer = torch.empty(**specs[key]).to(torch.device('cpu')).share_memory_()
                    _buffers[key].append(_buffer)
            buffers[device][player_id] = _buffers
    return buffers


def _decompose_training_plan(training_plan):
    parts = training_plan.split('_')
    player = parts[0]
    color_string = parts[1]
    color_map = {'v': 0, 'r': 1, 'w': 2, 'o': 3, 'b': 4, 'g': 5, 'p': 6}
    hand = [0] * 7
    for c in color_string:
        hand[color_map[c]] += 1
    preference_string = parts[2]
    geisha_preferences = {'first': [0] * 7, 'second': [0] * 7}
    for i, ch in enumerate(preference_string):
        if ch == 'f':
            geisha_preferences['first'][i] = 1
        elif ch == 's':
            geisha_preferences['second'][i] = 1
    elo_diff = int(parts[3])
    if len(parts) > 4:
        move_desc = parts[4]
    else:
        move_desc = None
    return [player, hand, geisha_preferences, elo_diff, move_desc]


def act(i, device, free_queue, full_queue, model, buffers, flags):
    """
    This function will run forever until we stop it. It will generate
    data from the environment and send the data to buffer. It uses
    a free queue and full queue to syncup with the main process.
    """
    player_ids = ['first', 'second']
    try:
        training_plan = None
        if flags.training_plan is not '':
            training_plan = _decompose_training_plan(flags.training_plan)

        T = flags.unroll_length
        log.info('Device %s Actor %i started.', str(device), i)

        env = create_env(flags)
        env = Environment(env, device)

        done_buf = {p: [] for p in player_ids}
        target_buf = {p: [] for p in player_ids}
        obs_x_no_move_buf = {p: [] for p in player_ids}
        obs_move_buf = {p: [] for p in player_ids}
        obs_z_buf = {p: [] for p in player_ids}
        size = {p: 0 for p in player_ids}
        acting_player_ids_by_round_id = {p: [] for p in player_ids}

        acting_player_id, round_id, obs, env_output = env.initial()

        while True:
            diff = {'first': 0, 'second': 0}
            while True:
                acting_player_ids_by_round_id[round_id].append(acting_player_id)
                obs_x_no_move_buf[round_id].append(env_output['obs_x_no_move'])
                obs_z_buf[round_id].append(env_output['obs_z'])
                with torch.no_grad():
                    agent_output = model.forward(round_id, obs['z_batch'], obs['x_batch'], flags=flags)
                _move_idx = int(agent_output['move'].cpu().detach().numpy())
                move = obs['moves'][_move_idx]
                obs_move_buf[round_id].append(my_move2tensor(move))
                size[round_id] += 1
                diff[round_id] += 1
                target_buf[round_id].append(None)
                acting_player_id, round_id, round_end_reward, obs, env_output = env.step(move)
                if round_end_reward is not None:
                    target_buf['first'][-6:] = [-round_end_reward] * 6
                    target_buf['second'][-6:] = [round_end_reward] * 6
                if env_output['done']:
                    result_glob = env_output['episode_result']
                    for p in player_ids:
                        # diff is the number of new training data valuated by model p
                        if diff[p] > 0:
                            done_buf[p].extend([False for _ in range(diff[p] - 1)])
                            done_buf[p].append(True)
                            acting_player_ids_by_round_id[p] = []
                        assert size[p] == len(target_buf[p])
                        assert size[p] == len(done_buf[p])
                    break

            for p in player_ids:
                while size[p] > T:
                    index = free_queue[p].get()
                    if index is None:
                        break
                    for t in range(T):
                        buffers[p]['done'][index][t, ...] = done_buf[p][t]
                        buffers[p]['target'][index][t, ...] = target_buf[p][t]
                        buffers[p]['obs_x_no_move'][index][t, ...] = obs_x_no_move_buf[p][t]
                        buffers[p]['obs_move'][index][t, ...] = obs_move_buf[p][t]
                        buffers[p]['obs_z'][index][t, ...] = obs_z_buf[p][t]
                    full_queue[p].put(index)
                    done_buf[p] = done_buf[p][T:]
                    target_buf[p] = target_buf[p][T:]
                    obs_x_no_move_buf[p] = obs_x_no_move_buf[p][T:]
                    obs_move_buf[p] = obs_move_buf[p][T:]
                    obs_z_buf[p] = obs_z_buf[p][T:]
                    size[p] -= T

    except KeyboardInterrupt:
        pass
    except Exception as e:
        log.error('Exception in worker process %i', i)
        traceback.print_exc()
        print()
        raise e
