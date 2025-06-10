import os 
import argparse
import pickle

from hanamikoji.env.game import get_card_play_data, get_card_play_data_training_plan
from hanamikoji.evaluation.simulation import evaluate
from hanamikoji.dmc.utils import _decompose_training_plan

if __name__ == '__main__':
    parser = argparse.ArgumentParser('Hanamikoji Evaluation')
    parser.add_argument('--first', type=str,
            default='baselines/hanamikojizero/first.ckpt')
    parser.add_argument('--second', type=str,
            default='baselines/hanamikojizero/second.ckpt')
    parser.add_argument('--num_workers', type=int, default=5)
    parser.add_argument('--gpu_device', type=str, default='')
    parser.add_argument('--num_games', type=int, default=10000)
    parser.add_argument('--training_plan', type=str, default='')
    args = parser.parse_args()

    os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
    os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu_device

    training_plan = None
    eval_data = 'eval_data_' + str(args.num_games) + '.pkl'
    if args.training_plan != '':
        training_plan = _decompose_training_plan(args.training_plan)
        eval_data = 'eval_data_' + args.training_plan + '_' + str(args.num_games) + '.pkl'

    if os.path.isfile(eval_data):
        print(f"{eval_data} exists.")
    else:
        print("output_pickle:", eval_data)
        print("generating data...")

        data = []
        for _ in range(args.num_games * 30):
            if training_plan is None:
                data.append(get_card_play_data())
            else:
                data.append(get_card_play_data_training_plan(training_plan))
        print("saving pickle file...")
        with open(eval_data, 'wb') as g:
            pickle.dump(data, g, pickle.HIGHEST_PROTOCOL)

    evaluate(args.first,
             args.second,
             eval_data,
             args.num_workers,
             training_plan,
             args.training_plan,
             args.num_games)
