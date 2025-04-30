import os
import sys
import argparse

from hanamikoji.evaluation.simulation import evaluate

if __name__ == '__main__':
    parser = argparse.ArgumentParser('Hanamikoji Evaluation')
    parser.add_argument('--first', type=str,
            default='baselines/hanamikojizero/first.ckpt')
    parser.add_argument('--second', type=str,
            default='baselines/hanamikojizero/second.ckpt')
    parser.add_argument('--eval_data', type=str,
            default='eval_data.pkl')
    parser.add_argument('--num_workers', type=int, default=5)
    parser.add_argument('--gpu_device', type=str, default='')
    args = parser.parse_args()

    os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
    os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu_device

    sys.stdout = open("output.txt", "w")
    evaluate(args.first,
             args.second,
             args.eval_data,
             args.num_workers)
