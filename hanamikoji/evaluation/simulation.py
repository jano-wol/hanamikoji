import multiprocessing as mp
import pickle

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

    glob = 0
    env = GameEnv(players)
    for idx, card_play_data in enumerate(card_play_data_list):
        env.card_play_init(card_play_data)
        while not env.winner:
            env.step()
        env.reset()
        if glob % 1000 == 0:
            print(glob)
        glob += 1

    q.put((env.num_wins['first'],
           env.num_wins['second']
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
