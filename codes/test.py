import os
import sys
import time
import random
import argparse
import numpy as np
from collections import OrderedDict

import torch
from torchvision.transforms import ToTensor

import options.options as option
import utils.util as util
import utils.metric as metric


# options
parser = argparse.ArgumentParser()
parser.add_argument('-opt', type=str, required=True, help='Path to options JSON file.')
args = parser.parse_args()
options_path = args.opt
opt = option.parse(options_path, is_train=False)
util.mkdirs((path for key , path in opt['path'].items() if not key == 'pretrain_model_G'))
opt = option.dict_to_nonedict(opt)

# print to file and std_out simultaneously
class PrintLogger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open(os.path.join(opt['path']['log'], 'print_log.txt'), "a")
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
    def flush(self):
        pass
sys.stdout = PrintLogger()

from data import create_dataset, create_dataloader
from models import create_model

# Create test dataset and dataloader
test_loaders = []
for phase, dataset_opt in opt['datasets'].items():
    test_set = create_dataset(dataset_opt)
    test_loader = create_dataloader(test_set, dataset_opt)
    test_size = len(test_set)
    test_set_name = dataset_opt['name']
    print('Number of test images in [%s]: %d' % (test_set_name, test_size))
    test_loaders.append(test_loader)

# Create model
model = create_model(opt)
model.eval()

# # Path for log file
# test_log_path = os.path.join(opt['path']['log'], 'test_log.txt')
# if os.path.exists(test_log_path):
#     os.remove(test_log_path)
#     print('Old test log is removed.')

print('Start Testing ...')

for test_loader in test_loaders:
    test_set_name = test_loader.dataset.opt['name']
    print('Testing [%s]...' % test_set_name)
    test_start_time = time.time()
    dataset_dir = os.path.join(opt['path']['results_root'], test_set_name)
    util.mkdir(dataset_dir)

    test_results = OrderedDict()
    test_results['psnr'] = []
    test_results['ssim'] = []

    for data in test_loader:
        need_HR = True
        if test_loader.dataset.opt['dataroot_HR'] is None:
            need_HR = False
        model.feed_data(data, volatile=True, need_HR=need_HR)
        img_path = data['LR_path'][0]

        img_name = os.path.splitext(os.path.basename(img_path))[0]

        model.test()  # test
        visuals = model.get_current_visuals(need_HR=need_HR)

        sr_img = util.tensor2img_np(visuals['SR']) # uint8

        if need_HR: # load GT image and calculate psnr
            gt_img = util.tensor2img_np(visuals['HR'])
            scale = test_loader.dataset.opt['scale']
            crop_border = scale
            cropped_sr_img = sr_img[crop_border:-crop_border, crop_border:-crop_border, :]
            cropped_gt_img = gt_img[crop_border:-crop_border, crop_border:-crop_border, :]
            psnr = metric.psnr(cropped_sr_img, cropped_gt_img)
            ssim = metric.ssim(cropped_sr_img, cropped_gt_img, multichannel=True)

            test_results['psnr'].append(psnr)
            test_results['ssim'].append(ssim)

            print('{:20s} - PSNR: {:.2f} dB; SSIM: {:.2f}'.format(img_name, psnr, ssim))
        else:
            print(img_name)

        save_img_path = os.path.join(dataset_dir, img_name+'.png')
        util.save_img_np(sr_img, save_img_path)

    # Average PSNR/SSIM results
    ave_psnr = sum(test_results['psnr'])/len(test_results['psnr'])
    ave_ssim = sum(test_results['ssim'])/len(test_results['ssim'])
    print('-----\nAverage PSNR/SSIM results for {}\n\tPSNR: {:.2f} dB; SSIM: {:.2f}\n-----'.format(\
        test_set_name, ave_psnr, ave_ssim))

