import os
import argparse

from hanamikoji.evaluation.human import Human
from hanamikoji.evaluation.deep_agent import DeepAgent
from hanamikoji.env.game import GameEnvExternal


def parse_args():
    parser = argparse.ArgumentParser('Hanamikoji Play')
    parser.add_argument('--ckpt_folder', type=str, default='baselines/')
    parser.add_argument('--gpu_device', type=str, default='')
    return parser.parse_args()


def setup_environment(args):
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
    os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu_device


def card_list_to_inner(l):
    ret = [0] * 7
    for c in l:
        ret[c - 1] += 1
    return ret


def inner_to_card_list(inner):
    ret = []
    for i, val in enumerate(inner):
        while val > 0:
            ret.append(i)
            val -= 1
    return ret


def parse_agent_player_id():
    while True:
        choice = input("Provide agent player id (first/second): ").strip().lower()
        if choice in {"first", "second"}:
            return choice
        print("Invalid input. Please enter 'first' or 'second'.")


def parse_starting_hand(agent_player_id):
    expected_length = 7 if agent_player_id == 'first' else 6
    while True:
        hand_str = input(f"Enter the agent's starting hand ({expected_length} digits, each 1–7): ").strip()
        if len(hand_str) != expected_length or not hand_str.isdigit():
            print(f"Invalid input. Please enter exactly {expected_length} digits.")
            continue
        hand = [int(c) for c in hand_str]
        if all(1 <= card <= 7 for card in hand):
            return hand
        print("Invalid card values. All digits must be between 1 and 7.")


def get_opp(curr):
    return 'first' if curr == 'second' else 'second'


def main():
    args = parse_args()
    setup_environment(args)

    agent = DeepAgent(args.ckpt_folder)

    # STEP_1 PARSE PLAYER ID
    agent_player_id = parse_agent_player_id()
    players = {agent_player_id: agent, get_opp(agent_player_id): Human()}
    env = GameEnvExternal(players)
    env.card_play_init()
    while env.winner is None:
        env.step()
    print(f'winner={players[env.winner]}')

if __name__ == '__main__':
    main()
