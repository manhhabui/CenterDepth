import _init_paths
import os
import argparse
import json
import torch
import numpy as np
import random

from algorithms.cd_regression_v1.src.trainer import Trainer_cd_regression_v1
from algorithms.cd_regression_v1.src.test import test
from algorithms.cd_regression_v1.src.demo import demo

def fix_random_seed(seed_value):
    random.seed(seed_value)
    np.random.seed(seed_value)
    torch.manual_seed(seed_value)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed_value)
        torch.cuda.manual_seed(seed_value)
        torch.backends.cudnn.enabled = False
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True

def parse(opt, bash_args):
    opt.exp_id = bash_args.exp_id
    opt.lr_step = [int(i) for i in opt.lr_step.split(',')]
    opt.test_scales = [1.0]

    opt.out_thresh = opt.track_thresh
    opt.pre_thresh = opt.track_thresh
    opt.new_thresh = opt.track_thresh
    opt.pre_img = True

    opt.fix_res = True

    opt.head_conv = 256 if 'dla' in opt.model else 64

    opt.pad = 127 if 'hourglass' in opt.model else 31
    opt.num_stacks = 2 if opt.model == 'hourglass' else 1

    # log dirs
    opt.root_dir = os.path.join(os.path.dirname(__file__), '..', '..')
    opt.data_dir = os.path.join(opt.root_dir, 'data')
    opt.exp_dir = os.path.join(opt.root_dir, 'exp', 'tracking')
    opt.save_dir = os.path.join(opt.exp_dir, bash_args.exp_id)
    
    opt.checkpoint_name = "algorithms/" + opt.algorithm + "/results/checkpoints/" + opt.exp_name + "_" + opt.exp_id + '.pt'

    opt.num_classes =  opt.num_classes
    opt.output_h = opt.input_h // 4
    opt.output_w = opt.input_w // 4
    opt.input_res = max(opt.input_h, opt.input_w)
    opt.output_res = max(opt.output_h, opt.output_w)
  
    opt.heads = {'hm': opt.num_classes, 'reg': 2, 'wh': 2, 'dep': 1, 'tracking': 2}

    weight_dict = {'hm': 1, 'wh': 0.1, 'reg': 1, 'dep': 1, 'tracking': 1}

    opt.weights = {head: weight_dict[head] for head in opt.heads}
    for head in opt.weights:
        if opt.weights[head] == 0:
            del opt.heads[head]
    opt.head_conv = {head: [opt.head_conv \
          for i in range(1 if head != 'reg' else 1)] for head in opt.heads}
    
    print('input h w:', opt.input_h, opt.input_w)
    print('heads', opt.heads)
    print('weights', opt.weights)
    print('head conv', opt.head_conv)

    return opt

algorithms_map = {
    'cd_regression_v1': Trainer_cd_regression_v1
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--config", help = "Path to configuration file")
    parser.add_argument("--exp_id", help = "Index of experiment")
    parser.add_argument("--gpu_id", help = "Index of GPU")
    bash_args = parser.parse_args()
    with open(bash_args.config, "r") as inp:
        args = argparse.Namespace(**json.load(inp))

    args = parse(args, bash_args)
    
    os.environ["CUDA_VISIBLE_DEVICES"] = bash_args.gpu_id  
    # torch.cuda.set_device(int(bash_args.gpu_id))
        
    # fix_random_seed(args.seed_value)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    trainer = algorithms_map[args.algorithm](args, device, bash_args.exp_id)
    trainer.train()
    trainer.test()
    print("Finished!")

    # demo(args)