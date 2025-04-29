"""
Here, we wrap the original environment to make it easier
to use. When a game is finished, instead of mannualy reseting
the environment, we do it automatically.
"""
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
    x_no_move = torch.from_numpy(obs['x_no_move'])
    z_batch = torch.from_numpy(obs['z_batch']).to(device)
    z = torch.from_numpy(obs['z'])
    obs = {'x_batch': x_batch,
           'z_batch': z_batch,
           'moves': obs['moves'],
           }
    return acting_player_id, round_id, obs, x_no_move, z

class Environment:
    def __init__(self, env, device):
        """
        Initialzie this environment wrapper
        """
        self.env = env
        self.device = device
        self.episode_return = None

    def initial(self):
        acting_player_id, round_id, initial_obs, x_no_move, z = _format_observation(self.env.reset(), self.device)
        self.episode_return = torch.zeros(1, 1)
        initial_done = torch.ones(1, 1, dtype=torch.bool)

        return acting_player_id, round_id, initial_obs, dict(
            done=initial_done,
            episode_return=self.episode_return,
            obs_x_no_move=x_no_move,
            obs_z=z
            )
        
    def step(self, move):
        obs, reward, done, _ = self.env.step(move)
        self.episode_return += reward
        episode_return = self.episode_return 

        if done:
            obs = self.env.reset()
            self.episode_return = torch.zeros(1, 1)

        acting_player_id, round_id, obs, x_no_move, z = _format_observation(obs, self.device)
        done = torch.tensor(done).view(1, 1)
        
        return acting_player_id, round_id, obs, dict(
            done=done,
            episode_return=episode_return,
            obs_x_no_move=x_no_move,
            obs_z=z
            )
