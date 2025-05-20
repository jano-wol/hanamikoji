import torch
from hanamikoji.dmc.models_clean import LstmModel

ckpt_path = "/home/jano/Repositories/hanamikoji/baselines/second.ckpt"  # or second, etc.

state_dict = torch.load(ckpt_path, map_location="cpu")
model = LstmModel()
model.load_state_dict(state_dict)
model.eval()
scripted = torch.jit.script(model)
scripted.save("second.pt")