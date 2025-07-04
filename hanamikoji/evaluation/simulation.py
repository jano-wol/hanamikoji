import multiprocessing as mp
import pickle
from copy import deepcopy

from hanamikoji.env.game import GameEnv


def load_card_play_models(card_play_model_path_dict):
    players = {}

    for player_id in ['first', 'second']:
        if card_play_model_path_dict[player_id] == 'random':
            from .random_agent import RandomAgent
            players[player_id] = RandomAgent()
        else:
            from .deep_agent import DeepAgent
            players[player_id] = DeepAgent(card_play_model_path_dict[player_id])
    return players


def mp_simulate(card_play_data_list, card_play_model_path_dict, q):
    players = load_card_play_models(card_play_model_path_dict)
    players_2 = {'first': players['second'], 'second': players['first']}
    envs = [GameEnv(players), GameEnv(players_2)]
    envs[0].card_play_data = envs[1].card_play_data = card_play_data_list
    for idx in range(10000):
        for env in envs:
            card_play_data = deepcopy(env.get_new_round_play_data())
            env.card_play_init(card_play_data)
            while not env.winner:
                env.step()
            env.reset()
        if idx % 1000 == 0:
            print(f'game={idx}, {envs[0].num_wins['first'] + envs[1].num_wins['second']} - {envs[0].num_wins['second'] + envs[1].num_wins['first']}')
    print(f'Final: {envs[0].num_wins['first'] + envs[1].num_wins['second']} - {envs[0].num_wins['second'] + envs[1].num_wins['first']}')
    q.put((envs[0].num_wins['first'] + envs[1].num_wins['second'],
           envs[0].num_wins['second'] + envs[1].num_wins['first']
           ))


def data_allocation_per_worker(card_play_data_list, num_workers):
    card_play_data_list_each_worker = [[] for k in range(num_workers)]
    for idx, data in enumerate(card_play_data_list):
        card_play_data_list_each_worker[idx % num_workers].append(data)

    return card_play_data_list_each_worker


def evaluate(first, second, eval_data, num_workers):
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
            args=(card_play_data, card_play_model_path_dict, q))
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
