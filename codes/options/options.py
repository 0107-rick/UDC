import os
from collections import OrderedDict
from datetime import datetime
import json


def get_timestamp():
    return datetime.now().strftime('%y%m%d-%H%M%S')


def parse(opt_path, is_train=True):
    # remove comments starting with '//'
    json_str = ''
    with open(opt_path, 'r') as f:
        for line in f:
            line = line.split('//')[0] + '\n'
            json_str += line
    opt = json.loads(json_str, object_pairs_hook=OrderedDict)
    opt['timestamp'] = get_timestamp()
    opt['is_train'] = is_train

    for key, path in opt['path'].items():
        opt['path'][key] = os.path.expanduser(path)
    for phase, dataset in opt['datasets'].items():
        dataset['phase'] = phase
        if dataset['dataroot_HR'] is not None:
            dataset['dataroot_HR'] = os.path.expanduser(dataset['dataroot_HR'])
        if dataset['dataroot_LR'] is not None:
            dataset['dataroot_LR'] = os.path.expanduser(dataset['dataroot_LR'])
        if phase == 'train' and dataset['subset_file'] is not None:
            dataset['subset_file'] = os.path.expanduser(dataset['subset_file'])

    if is_train:
        experiments_root = os.path.join(opt['path']['root'], 'experiments', opt['name'])
        opt['path']['experiments_root'] = experiments_root
        opt['path']['options'] = experiments_root
        opt['path']['models'] = os.path.join(experiments_root, 'models')
        opt['path']['log'] = experiments_root
        opt['path']['val_images'] = os.path.join(experiments_root, 'val_images')

        # change some options for debug mode
        if 'debug' in opt['name']:
            opt['train']['val_freq'] = 8
            opt['logger']['print_freq'] = 2
            opt['logger']['save_checkpoint_freq'] = 8
            opt['train']['lr_decay_iter'] = 10
    else: # test
        results_root = os.path.join(opt['path']['root'], 'results', opt['name'])
        opt['path']['results_root'] = results_root
        opt['path']['options'] = results_root
        opt['path']['log'] = results_root
    return opt

def save(opt):
    dump_dir = opt['path']['options']
    dump_path = os.path.join(dump_dir, 'options.json')
    with open(dump_path, 'w') as dump_file:
        json.dump(opt, dump_file, indent=2)


class NoneDict(dict):
    def __missing__(self, key):
        return None

# convert to NoneDict, which return None for missing key.
def dict_to_nonedict(opt):
    if isinstance(opt, dict):
        new_opt = dict()
        for key, sub_opt in opt.items():
            new_opt[key] = dict_to_nonedict(sub_opt)
        return NoneDict(**new_opt)
    elif isinstance(opt, list):
        return [dict_to_nonedict(sub_opt) for sub_opt in opt]
    else:
        return opt
