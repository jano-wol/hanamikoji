import argparse
import os
import json

from hanamikoji.evaluation.deep_agent import DeepAgent
from hanamikoji.evaluation.human import Human
from hanamikoji.env.game import GameEnv, get_card_play_data

AGENT_OUT_PATH = "agent_out.json"
HUMAN_IN_PATH = "human_in.json"
POLL_INTERVAL = 0.5  # seconds


def parse_args():
    parser = argparse.ArgumentParser('Hanamikoji Play')
    parser.add_argument('--ckpt_folder', type=str, default='baselines/')
    parser.add_argument('--gpu_device', type=str, default='')
    return parser.parse_args()


def clear_environment():
    if os.path.exists(AGENT_OUT_PATH):
        os.remove(AGENT_OUT_PATH)
    if os.path.exists(HUMAN_IN_PATH):
        os.remove(HUMAN_IN_PATH)


def setup_environment(args):
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
    os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu_device
    clear_environment()


def write_state(env, tick):
    with open(AGENT_OUT_PATH, 'w') as f:
        d = {tick: env.to_dict()}
        f.write(json.dumps(d))
    print(f"State written.")


def get_human_id(players):
    if isinstance(players['first'], Human):
        return 'first'
    if isinstance(players['second'], Human):
        return 'second'
    return None


def get_opp(curr):
    return 'first' if curr == 'second' else 'second'


def get_human(players):
    human_id = get_human_id(players)
    if human_id is None:
        return None
    return players[human_id]


def tidy_up(env, players, ):
    env.reset()
    env.players = players
    env.card_play_init(get_card_play_data())
    clear_environment()


def swap_players(env, players, ):
    human_id = get_human_id(players)
    opp = get_opp(human_id)
    players[human_id] = players[opp]
    players[opp] = Human(HUMAN_IN_PATH, POLL_INTERVAL)
    tidy_up(env, players, )


def reset_players(env, players, ):
    human_id = get_human_id(players)
    players[human_id] = Human(HUMAN_IN_PATH, POLL_INTERVAL)
    tidy_up(env, players, )


def handle_human_interrupt(env, players, ):
    human = get_human(env.players)
    if human is None:
        return False
    human.check_interrupt()
    if human.interrupt == "swap":
        swap_players(env, players, )
        return True
    if human.interrupt == "reset":
        reset_players(env, players, )
        return True
    return False


def main():
    args = parse_args()
    setup_environment(args)

    players = {'first': Human(HUMAN_IN_PATH, POLL_INTERVAL), 'second': DeepAgent(args.ckpt_folder)}
    # players = {'first': DeepAgent(args.ckpt_folder), 'second': DeepAgent(args.ckpt_folder)}
    env = GameEnv(players)
    env.card_play_init(get_card_play_data())
    print("Agent backend started.")

    tick = 1
    while True:
        write_state(env, tick)
        tick += 1
        env.step()
        interrupt = handle_human_interrupt(env, players)
        if interrupt:
            tick = 1
            continue
        if env.winner:
            write_state(env, tick)
            while True:
                human_id = get_human_id(players)
                if human_id is not None:
                    interrupt = handle_human_interrupt(env, players)
                    if interrupt:
                        tick = 1
                        break
                else:
                    tidy_up(env, players)
                    tick = 1
                    break


if __name__ == '__main__':
    main()
