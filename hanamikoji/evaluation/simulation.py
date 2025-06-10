import multiprocessing as mp
import pickle
from copy import deepcopy

from hanamikoji.env.game import GameEnv
from hanamikoji.evaluation.deep_agent import DeepAgent


def load_card_play_models(card_play_model_path_dict):
    players = {}

    for player_id in ['first', 'second']:
        if card_play_model_path_dict[player_id] == 'random':
            from .random_agent import RandomAgent
            players[player_id] = RandomAgent()
        else:
            players[player_id] = DeepAgent(card_play_model_path_dict[player_id])
    return players


def mp_simulate(card_play_data_list, card_play_model_path_dict, training_plan, training_plan_str, num_games, q):
    if training_plan is None:
        players = load_card_play_models(card_play_model_path_dict)
        players_2 = {'first': players['second'], 'second': players['first']}
        envs = [GameEnv(players, training_plan), GameEnv(players_2, training_plan)]
        envs[0].card_play_data = envs[1].card_play_data = card_play_data_list
        for idx in range(num_games):
            for env in envs:
                card_play_data = deepcopy(env.get_new_round_play_data())
                env.card_play_init(card_play_data)
                while not env.winner:
                    env.step()
                env.reset()
            if idx % 1000 == 0:
                v_1 = envs[0].num_wins['first'] + envs[1].num_wins['second']
                v_2 = envs[0].num_wins['second'] + envs[1].num_wins['first']
                print(f'game={idx}, {v_1} - {v_2}')
        v_1 = envs[0].num_wins['first'] + envs[1].num_wins['second']
        v_2 = envs[0].num_wins['second'] + envs[1].num_wins['first']
        print(f'Final: {v_1} - {v_2}')
        q.put((envs[0].num_wins['first'] + envs[1].num_wins['second'],
               envs[0].num_wins['second'] + envs[1].num_wins['first']))
    else:
        players = {'first': DeepAgent.default_player(), 'second': DeepAgent.default_player()}
        if training_plan[0] == 'first':
            players_2 = {'first': DeepAgent.from_training_plan(training_plan, training_plan_str),
                         'second': DeepAgent.default_player()}
        else:
            players_2 = {'first': DeepAgent.default_player(),
                         'second': DeepAgent.from_training_plan(training_plan, training_plan_str)}
        envs = [GameEnv(players, training_plan), GameEnv(players_2, training_plan)]
        envs[0].card_play_data = envs[1].card_play_data = card_play_data_list
        p = [0.0, 0.0]
        for idx in range(num_games):
            for i, env in enumerate(envs):
                env.reset()
                card_play_data = deepcopy(env.get_new_round_play_data())
                env.card_play_init(card_play_data)
                while env.round_end_reward is None:
                    env.step()
                if env.round_end_reward < 0:
                    env.num_wins['first'] += 1
                else:
                    env.num_wins['second'] += 1
                p_first_win = 0.5 + (-env.round_end_reward) / 2.0
                p[i] += p_first_win
                env.reset()
            if idx % 10 == 0:
                if training_plan[0] == 'first':
                    print(
                        f'games finished={idx + 1}, first.ckpt win_chance={p[0] / float(idx + 1)}  {training_plan_str}.ckpt win_chance={p[1] / float(idx + 1)}')
                if training_plan[0] == 'second':
                    print(
                        f'games finished={idx + 1}, second.ckpt win_chance={1 - (p[0] / float(idx + 1))}  {training_plan_str}.ckpt win_chance={1 - (p[1] / float(idx + 1))}')
        if training_plan[0] == 'first':
            print(
                f'Final. first.ckpt win_chance={p[0] / float(idx + 1)}  {training_plan_str}.ckpt win_chance={p[1] / float(idx + 1)}')
        if training_plan[0] == 'second':
            print(
                f'Final. second.ckpt win_chance={1 - (p[0] / float(idx + 1))}  {training_plan_str}.ckpt win_chance={1 - (p[1] / float(idx + 1))}')
        q.put((envs[0].num_wins['first'] + envs[1].num_wins['second'],
               envs[0].num_wins['second'] + envs[1].num_wins['first']))


def data_allocation_per_worker(card_play_data_list, num_workers):
    card_play_data_list_each_worker = [[] for k in range(num_workers)]
    for idx, data in enumerate(card_play_data_list):
        card_play_data_list_each_worker[idx % num_workers].append(data)

    return card_play_data_list_each_worker


def evaluate(first, second, eval_data, num_workers, training_plan, training_plan_str, num_games):
    with open(eval_data, 'rb') as f:
        card_play_data_list = pickle.load(f)

    card_play_data_list_each_worker = data_allocation_per_worker(
        card_play_data_list, num_workers)
    del card_play_data_list

    card_play_model_path_dict = {
        'first': first,
        'second': second
    }

    num_first_wins = 0
    num_second_wins = 0

    ctx = mp.get_context('spawn')
    q = ctx.SimpleQueue()
    processes = []
    for card_play_data in card_play_data_list_each_worker:
        p = ctx.Process(
            target=mp_simulate,
            args=(card_play_data, card_play_model_path_dict, training_plan, training_plan_str, num_games, q))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    for i in range(num_workers):
        result = q.get()
        num_first_wins += result[0]
        num_second_wins += result[1]

    num_total_wins = num_first_wins + num_second_wins
    print('Results:')
    print('first : second - {} : {}'.format(num_first_wins / num_total_wins, num_second_wins / num_total_wins))
