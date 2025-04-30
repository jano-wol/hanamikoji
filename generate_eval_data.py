import argparse
import pickle
import numpy as np
from hanamikoji.env.game import get_card_play_data


def get_parser():
    parser = argparse.ArgumentParser(description='HanamikojiZero: random data generator')
    parser.add_argument('--output', default='eval_data', type=str)
    parser.add_argument('--num_games', default=10000, type=int)
    return parser


if __name__ == '__main__':
    flags = get_parser().parse_args()
    output_pickle = flags.output + '.pkl'

    print("output_pickle:", output_pickle)
    print("generating data...")

    data = []
    for _ in range(flags.num_games):
        data.append(get_card_play_data())

    print("saving pickle file...")
    with open(output_pickle, 'wb') as g:
        pickle.dump(data, g, pickle.HIGHEST_PROTOCOL)
