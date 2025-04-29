"""
Here, we wrap the original environment to make it easier
to use. When a game is finished, instead of mannualy reseting
the environment, we do it automatically.
"""
import numpy as np
import torch 

def _format_observation(obs, device):
    """
    A utility function to process observations and
    move them to CUDA.
    """
    acting_player_id = obs['id']
    round_id = obs['round_id']
    if not device == "cpu":
        device = 'cuda:' + str(device)
    device = torch.device(device)
    x_batch = torch.from_numpy(obs['x_batch']).to(device)
    z_batch = torch.from_numpy(obs['z_batch']).to(device)
    z = torch.from_numpy(obs['z'])
    obs = {'x_batch': x_batch,
           'z_batch': z_batch,
           'moves': obs['moves'],
           }
    return acting_player_id, round_id, obs, z

class Environment:
    def __init__(self, env, device):
        """
        Initialzie this environment wrapper
        """
        self.env = env
        self.device = device
        self.episode_return = None

    def initial(self):
        acting_player_id, round_id, initial_obs, z = _format_observation(self.env.reset(), self.device)
        self.episode_return = torch.zeros(1, 1)
        initial_done = torch.ones(1, 1, dtype=torch.bool)

        return acting_player_id, round_id, initial_obs, dict(
            done=initial_done,
            episode_return=self.episode_return,
            obs_z=z
            )
        
    def step(self, action):
        obs, reward, done, _ = self.env.step(action)
        self.episode_return += reward
        episode_return = self.episode_return 

        if done:
            obs = self.env.reset()
            self.episode_return = torch.zeros(1, 1)

        acting_player_id, round_id, obs, z = _format_observation(obs, self.device)
        done = torch.tensor(done).view(1, 1)
        
        return acting_player_id, round_id, obs, dict(
            done=done,
            episode_return=episode_return,
            obs_z=z
            )
