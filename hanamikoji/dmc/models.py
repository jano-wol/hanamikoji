"""
This file includes the torch models. We wrap the three
models into one class for convenience.
"""

import numpy as np

import torch
from torch import nn
from hanamikoji.env.env import MOVE_VECTOR_SIZE, X_FEATURE_SIZE
from hanamikoji.dmc.utils import BELIEF_OUT


class BeliefModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(MOVE_VECTOR_SIZE, 128, batch_first=True)
        self.dense1 = nn.Linear(X_FEATURE_SIZE + 128, 512)
        self.dense2 = nn.Linear(512, 512)
        self.dense3 = nn.Linear(512, 512)
        self.dense4 = nn.Linear(512, BELIEF_OUT)

    def forward(self, z, x):
        lstm_out, (h_n, _) = self.lstm(z)
        lstm_out = lstm_out[:, -1, :]
        x = torch.cat([lstm_out, x], dim=-1)
        x = self.dense1(x)
        x = torch.relu(x)
        x = self.dense2(x)
        x = torch.relu(x)
        x = self.dense3(x)
        x = torch.relu(x)
        x = self.dense4(x)
        return dict(values=x)


class LstmModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(MOVE_VECTOR_SIZE, 128, batch_first=True)
        self.dense1 = nn.Linear(X_FEATURE_SIZE + BELIEF_OUT + 128, 512)
        self.dense2 = nn.Linear(512, 512)
        self.dense3 = nn.Linear(512, 512)
        self.dense4 = nn.Linear(512, 512)
        self.dense5 = nn.Linear(512, 512)
        self.dense6 = nn.Linear(512, 1)

    def forward(self, z, x, belief_out, return_value=False, flags=None):
        lstm_out, (h_n, _) = self.lstm(z)
        lstm_out = lstm_out[:, -1, :]
        x = torch.cat([lstm_out, x, belief_out], dim=-1)
        x = self.dense1(x)
        x = torch.relu(x)
        x = self.dense2(x)
        x = torch.relu(x)
        x = self.dense3(x)
        x = torch.relu(x)
        x = self.dense4(x)
        x = torch.relu(x)
        x = self.dense5(x)
        x = torch.relu(x)
        x = self.dense6(x)
        if return_value:
            return dict(values=x)
        else:
            if flags is not None and flags.exp_epsilon > 0 and np.random.rand() < flags.exp_epsilon:
                move = torch.randint(x.shape[0], (1,))[0]
            else:
                move = torch.argmax(x, dim=0)[0]
            return dict(move=move)


# Model dict is only used in evaluation but not training
model_dict = {'first': LstmModel, 'second': LstmModel, 'belief': BeliefModel}


class Model:
    """
    The wrapper for the three models. We also wrap several
    interfaces such as share_memory, eval, etc.
    """

    def __init__(self, device=0):
        self.models = {}
        if not device == "cpu":
            device = 'cuda:' + str(device)
        self.models['first'] = LstmModel().to(torch.device(device))
        self.models['second'] = LstmModel().to(torch.device(device))
        self.models['belief'] = BeliefModel().to(torch.device(device))

    def forward(self, player_id, z, x, training=False, flags=None):
        model = self.models[player_id]
        belief_model = self.models['belief']
        belief_out = belief_model.forward(z, x)
        return model.forward(z, x, belief_out['values'], training, flags)

    def share_memory(self):
        self.models['first'].share_memory()
        self.models['second'].share_memory()
        self.models['belief'].share_memory()

    def eval(self):
        self.models['first'].eval()
        self.models['second'].eval()
        self.models['belief'].eval()

    def parameters(self, player_id):
        return self.models[player_id].parameters()

    def get_model(self, player_id):
        return self.models[player_id]

    def get_models(self):
        return self.models
