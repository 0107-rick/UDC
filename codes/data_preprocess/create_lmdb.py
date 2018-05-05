import os.path
import lmdb
import numpy as np
import glob
import cv2

# img_path should contains glob matching pattern
img_path = '/mnt/SSD/xtwang/BasicSR_datasets/DIV2K800_new/DIV2K800_sub_bicLRx2/*'
lmdb_save_path = '/mnt/SSD/xtwang/BasicSR_datasets/DIV2K800_new/DIV2K800_sub_bicLRx2.lmdb'

file_list = sorted(glob.glob(img_path))
dataset = []
data_size = 0
print('Read image...')
for i in range(len(file_list)):
    if i % 100 == 0:
        print(i)
    img = cv2.imread(file_list[i], cv2.IMREAD_UNCHANGED)
    dataset.append(img)
    data_size += img.nbytes
map_size = data_size * 10
env = lmdb.open(lmdb_save_path, map_size=map_size)

print('Finish reading image.\nWrite to lmdb')
with env.begin(write=True) as txn:
    # txn is a Transaction object
    for i in range(len(file_list)):
        if i % 100 == 0:
            print(i)
        img_name = os.path.splitext(os.path.basename(file_list[i]))[0]
        key = img_name.encode('ascii')
        data = dataset[i]
        if dataset[i].ndim == 2:
            H, W = dataset[i].shape
            C = 1
        else:
            H, W, C = dataset[i].shape
        meta_key = (img_name + '.meta').encode('ascii')
        meta = '{:d},{:d},{:d}'.format(H,W,C)
        # The encode is only essential in Python 3
        txn.put(key, data)
        txn.put(meta_key, meta.encode('ascii'))


# test lmdb
'''
env = lmdb.open('./test.lmdb', readonly=True)
# get all the keys
with env.begin(write=False) as txn:
    keys = [key.decode('ascii') for key, _ in txn.cursor()]
keys = [key for key in keys if not key.endswith('.meta')]
keys_byte = [key.encode('ascii') for key in keys]
keys_meta_byte = [(key+'.meta').encode('ascii') for key in keys]


with env.begin(write=False) as txn:
    buf = txn.get(keys_byte[0])
    buf_meta = txn.get(keys_meta_byte[0])

flat_img_data = np.frombuffer(buf, dtype=np.uint8)
meta_str = buf_meta.decode('ascii')
H, W, C = [int(s) for s in meta_str.split(',')]
img_data = flat_img_data.reshape(H, W, C)
'''
