import torch
from hanamikoji.dmc.models_clean import LstmModel

for p in ['first', 'second']:
    ckpt_path = f"./baselines/{p}.ckpt"
    state_dict = torch.load(ckpt_path, map_location="cpu")
    model = LstmModel()
    model.load_state_dict(state_dict)
    model.eval()
    scripted = torch.jit.script(model)
    scripted.save(f'./baselines/{p}.pt')
