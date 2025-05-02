import os 
import argparse

from hanamikoji.evaluation.deep_agent import DeepAgent
from hanamikoji.env.game import GameState, PrivateInfoSet

if __name__ == '__main__':
    parser = argparse.ArgumentParser('Hanamikoji Play')
    parser.add_argument('--ckpt_folder', type=str,default='baselines/')
    parser.add_argument('--gpu_device', type=str, default='')
    args = parser.parse_args()
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
    os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu_device
    agent = DeepAgent(args.ckpt_folder)

