"""
This file includes the torch models. We wrap the three
models into one class for convenience.
"""

import torch
from torch import nn
from hanamikoji.env.env import MOVE_VECTOR_SIZE, X_FEATURE_SIZE


class LstmModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(MOVE_VECTOR_SIZE, 128, batch_first=True)
        self.dense1 = nn.Linear(X_FEATURE_SIZE + 128, 512)
        self.dense2 = nn.Linear(512, 512)
        self.dense3 = nn.Linear(512, 512)
        self.dense4 = nn.Linear(512, 512)
        self.dense5 = nn.Linear(512, 512)
        self.dense6 = nn.Linear(512, 1)

    def forward(self, z: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
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
        x = torch.relu(x)
        x = self.dense5(x)
        x = torch.relu(x)
        x = self.dense6(x)
        return x
