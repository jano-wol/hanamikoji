import argparse
from copy import deepcopy
import os
import time
import json

from hanamikoji.evaluation.deep_agent import DeepAgent
from hanamikoji.evaluation.human import Human
from hanamikoji.env.game import GameEnv, get_card_play_data

AGENT_OUT_PATH = "agent_out.json"
GAME_PATH = "game_out.json"
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
    if os.path.exists(GAME_PATH):
        os.remove(GAME_PATH)


def setup_environment(args):
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
    os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu_device
    clear_environment()


def to_dict(env):
    def player_repr(p):
        if isinstance(p, DeepAgent):
            return "DeepAgent"
        elif isinstance(p, Human):
            return "Human"
        else:
            return str(p)

    return deepcopy({
        "players": {
            role: player_repr(p)
            for role, p in env.players.items()
        },
        "deck": env.deck,
        "round": env.round,
        "winner": env.winner,
        "state": env.state.to_dict(),
        "private_info_sets": {"first": env.private_info_sets["first"].to_dict(),
                              "second": env.private_info_sets["second"].to_dict()}
    })


def write_state(env, tick):
    with open(AGENT_OUT_PATH, 'w') as f:
        d = {tick: to_dict(env)}
        f.write(json.dumps(d))
    print(f"State written.")


def write_game(all_states):
    with open(GAME_PATH, 'w') as f:
        f.write(json.dumps(all_states))
    print(f"Game written.")


def add_all_states(env, tick, all_states):
    all_states[tick] = to_dict(env)


def wait_for_human_response(last_mod_time=None):
    print("Waiting for human response...")
    while True:
        if os.path.exists(HUMAN_IN_PATH):
            current_mod_time = os.path.getmtime(HUMAN_IN_PATH)
            if last_mod_time is None or current_mod_time > last_mod_time:
                with open(HUMAN_IN_PATH, 'r') as f:
                    response = f.read().strip()
                print(f"Human move received: {response}")
                return response, current_mod_time
        time.sleep(POLL_INTERVAL)


def agent_play_turn():
    # This is a placeholder. Replace with actual move logic.
    return "AGENT_PLAY_CARD:3"


def process_human_response(response: str):
    # Parse and apply human response to game state
    print(f"Processing human response: {response}")
    # Update game state here


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


def tidy_up(env, players, all_states):
    env.reset()
    env.players = players
    env.card_play_init(get_card_play_data())
    clear_environment()
    all_states.clear()


def swap_players(env, players, all_states):
    human_id = get_human_id(players)
    opp = get_opp(human_id)
    players[human_id] = players[opp]
    players[opp] = Human(HUMAN_IN_PATH, POLL_INTERVAL)
    tidy_up(env, players, all_states)


def reset_players(env, players, all_states):
    human_id = get_human_id(players)
    players[human_id] = Human(HUMAN_IN_PATH, POLL_INTERVAL)
    tidy_up(env, players, all_states)


def handle_human_interrupt(env, players, all_states):
    human = get_human(env.players)
    if human is None:
        return False
    human.check_interrupt()
    if human.interrupt == "swap":
        swap_players(env, players, all_states)
        return True
    if human.interrupt == "reset":
        reset_players(env, players, all_states)
        return True
    return False


def main():
    args = parse_args()
    setup_environment(args)

    players = {'first': DeepAgent(args.ckpt_folder), 'second': DeepAgent(args.ckpt_folder)}
    env = GameEnv(players)
    env.card_play_init(get_card_play_data())
    print("Agent backend started. Playing as first player.")
    all_states = {}

    tick = 1
    while True:
        # Agent makes a move
        # move = agent_play_turn()
        # env.step(move)
        write_state(env, tick)
        add_all_states(env, tick, all_states)
        tick += 1
        env.step()
        interrupt = handle_human_interrupt(env, players, all_states)
        if interrupt:
            continue
        if env.winner:
            write_state(env, tick)
            add_all_states(env, tick, all_states)
            write_game(all_states)
            while True:
                human_id = get_human_id(players)
                if human_id is not None:
                    interrupt = handle_human_interrupt(env, players, all_states)
                    if interrupt:
                        break
                else:
                    return

        # Wait for human response
        # response, mod_time = wait_for_human_response(mod_time)
        # process_human_response(response)

        # Game over check can go here
        # if game.is_over(): break


if __name__ == '__main__':
    main()
