import argparse
import os
import time
import json

from hanamikoji.evaluation.deep_agent import DeepAgent
from hanamikoji.evaluation.human import Human
from hanamikoji.env.game import GameEnv

AGENT_OUT_PATH = "agent_out.json"
HUMAN_IN_PATH = "human_in.json"
POLL_INTERVAL = 0.5  # seconds

def parse_args():
    parser = argparse.ArgumentParser('Hanamikoji Play')
    parser.add_argument('--ckpt_folder', type=str, default='baselines/')
    parser.add_argument('--gpu_device', type=str, default='')
    return parser.parse_args()


def setup_environment(args):
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
    os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu_device


def to_dict(env):
    def player_repr(p):
        if isinstance(p, DeepAgent):
            return "DeepAgent"
        elif isinstance(p, Human):  # assuming you have a Human class
            return "Human"
        else:
            return str(p)  # fallback for unknown types
    return {
        "players": {
            player_repr(p): role
            for role, p in env.players.items()
        }
    }

def write_state(env):
    with open(AGENT_OUT_PATH, 'w') as f:
        f.write(json.dumps(to_dict(env)))
    print(f"State written.")


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


def main():
    args = parse_args()
    setup_environment(args)

    players = {}
    players['first'] = DeepAgent(args.ckpt_folder)
    players['second'] = Human()
    env = GameEnv(players)
    print("Agent backend started. Playing as first player.")


    # Assume GameState and agent are initialized here
    mod_time = None

    while True:
        # Agent makes a move
        #move = agent_play_turn()
        #env.step(move)
        write_state(env)

        # Wait for human response
        response, mod_time = wait_for_human_response(mod_time)
        process_human_response(response)

        # Game over check can go here
        # if game.is_over(): break


if __name__ == '__main__':
    main()
