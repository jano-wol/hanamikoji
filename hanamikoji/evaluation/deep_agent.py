import torch
import numpy as np

from hanamikoji.env.env import get_obs

def _load_model(round_id, ckpt_dir_path):
    from hanamikoji.dmc.models import model_dict
    ckpt_path = ckpt_dir_path + '/' + round_id + '.ckpt'
    model = model_dict[round_id]()
    model_state_dict = model.state_dict()
    if torch.cuda.is_available():
        pretrained = torch.load(ckpt_path, map_location='cuda:0')
    else:
        pretrained = torch.load(ckpt_path, map_location='cpu')
    pretrained = {k: v for k, v in pretrained.items() if k in model_state_dict}
    model_state_dict.update(pretrained)
    model.load_state_dict(model_state_dict)
    if torch.cuda.is_available():
        model.cuda()
    model.eval()
    return model

class DeepAgent:

    def __init__(self, ckpt_dir_path):
        self.model_first = _load_model('first', ckpt_dir_path)
        self.model_second = _load_model('second', ckpt_dir_path)

    def act(self, infoset):
        if len(infoset[1].moves) == 1:
            return infoset[1].moves[0]

        obs = get_obs(infoset)

        curr = infoset[0].acting_player_id
        opp = 'first' if curr == 'second' else 'second'

        z_batch = torch.from_numpy(obs['z_batch']).float()
        x_batch = torch.from_numpy(obs['x_batch']).float()

        x_batch1 = obs['x_batch']
        x_no_move1 = obs['x_no_move']

        # Step 1: Extract the first 106 elements from each row
        x_batch_prefix = x_batch1[:, :106]
        if not np.array_equal(x_no_move1[0:7], np.array([2, 2, 2, 3, 3, 4, 5])):
            raise ValueError("Error1.")
        if not np.array_equal(x_no_move1[7:14], np.array(infoset[0].geisha_preferences[curr]) - np.array(infoset[0].geisha_preferences[opp])):
            raise ValueError("Error2.")
        if not np.array_equal(x_no_move1[14:21], np.array(infoset[1].hand_cards)):
            raise ValueError("Error3.")
        if infoset[1].stashed_card is not None:
            if not np.array_equal(x_no_move1[21:28], np.array(infoset[1].stashed_card)):
                raise ValueError("Error4.")
        else:
            if not np.array_equal(x_no_move1[21:28], np.array([0, 0, 0, 0, 0, 0, 0])):
                raise ValueError("Error5.")
        if infoset[1].trashed_cards is not None:
            if not np.array_equal(x_no_move1[28:35], np.array(infoset[1].trashed_cards)):
                raise ValueError("Error6.")
        else:
            if not np.array_equal(x_no_move1[28:35], np.array([0, 0, 0, 0, 0, 0, 0])):
                raise ValueError("Error7.")
        # Step 2: Ensure all float values are integer-like (e.g., 1.0, 2.0, etc.)
        if not np.allclose(x_batch_prefix, np.round(x_batch_prefix)):
            raise ValueError("Some float values in x_batch[:, :106] are not integer-like.")

        # Step 3: Round and cast to int for accurate comparison
        x_batch_int = np.round(x_batch_prefix).astype(int)

        # Step 4: Compare to x_no_move across all rows
        comparison = x_batch_int == x_no_move1  # shape: (112, 106)

        # Step 5: Identify rows that fail
        rows_with_mismatch = np.where(~np.all(comparison, axis=1))[0]

        if rows_with_mismatch.size == 0:
            x = 0
        else:
            raise ValueError(f" Mismatch found in rows: {rows_with_mismatch}")

        #print_obs2(obs)

        if torch.cuda.is_available():
            z_batch, x_batch = z_batch.cuda(), x_batch.cuda()
        if infoset[0].id_to_round_id[infoset[0].acting_player_id] == 'first':
            y_pred = self.model_first.forward(z_batch, x_batch, return_value=True)['values']
        else:
            y_pred = self.model_second.forward(z_batch, x_batch, return_value=True)['values']
        y_pred = y_pred.detach().cpu().numpy()

        best_move_index = np.argmax(y_pred, axis=0)[0]
        best_move = infoset[1].moves[best_move_index]

        return best_move


def print_obs1(obs):
    x_no_move = obs['x_no_move']
    print(f'const={x_no_move[0:7]}')
    print(f'gpref={x_no_move[7:14]}')
    print(f'handc={x_no_move[14:21]}')
    print(f'stash={x_no_move[21:28]}')
    print(f'trash={x_no_move[28:35]}')
    print(f'dec12={x_no_move[35:42]}')
    print(f'dc221={x_no_move[42:49]}')
    print(f'dc222={x_no_move[49:56]}')
    print(f'actcu={x_no_move[56:60]}')
    print(f'actop={x_no_move[60:64]}')
    print(f'gifcu={x_no_move[64:71]}')
    print(f'gifop={x_no_move[71:78]}')
    print(f'gilal={x_no_move[78:85]}')
    print(f'ncrcu={x_no_move[85:92]}')
    print(f'ncrop={x_no_move[92:99]}')
    print(f'unknw={x_no_move[99:106]}')

def print_obs2(obs):
    z = obs['z']
    for i in z:
        print(i)