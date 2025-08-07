import os
import gzip
import numpy as np
import random
import shutil
from PIL import Image
from collections import defaultdict
import sys

def deleteAllFolder(path):
    for file_name in os.listdir(path):
        file_path = os.path.join(path, file_name)
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)

def downloadSaveData():
    train_data_file = 'train-images-idx3-ubyte.gz'
    train_labels_file = 'train-labels-idx1-ubyte.gz'
    data_dir = 'mnist_data'

    if os.path.exists(data_dir):
        deleteAllFolder(data_dir)
    else:
        os.makedirs(data_dir)

    with gzip.open(os.path.join(data_dir, train_data_file), 'rb') as f:
        train_images = np.frombuffer(f.read(), dtype=np.uint8, offset=16).reshape((-1, 28, 28))
    with gzip.open(os.path.join(data_dir, train_labels_file), 'rb') as f:
        train_labels = np.frombuffer(f.read(), dtype=np.uint8, offset=8)

    out_dir = 'mnist_data/images'
    os.makedirs(out_dir, exist_ok=True)

    for i, (img, label) in enumerate(zip(train_images, train_labels)):
        img = Image.fromarray(img, mode='L')
        label_dir = os.path.join(out_dir, str(label))
        os.makedirs(label_dir, exist_ok=True)
        img.save(os.path.join(label_dir, f'{i}.jpg'))

def split_data_non_iid_quantity(input_dir, output_dir, n_clients):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # First collect all files by label
    label_files = defaultdict(list)
    for label in range(10):
        label_path = os.path.join(input_dir, str(label))
        if os.path.exists(label_path):
            files = [f for f in os.listdir(label_path) if f.endswith('.jpg')]
            random.shuffle(files)  # Shuffle each class's files
            label_files[label] = [os.path.join(label_path, f) for f in files]

    # Create client directories
    for i in range(n_clients):
        client_dir = os.path.join(output_dir, f'client_{i}')
        os.makedirs(client_dir, exist_ok=True)

    # Create skewed distribution (power law) for quantities
    base_quantities = np.random.power(0.6, n_clients)
    base_quantities = (base_quantities / base_quantities.min()).astype(int)

    # Distribute files to clients with quantity skew
    for label in range(10):
        files = label_files[label]
        total_files = len(files)
        
        # Calculate distribution for this label
        weights = np.random.power(0.5, n_clients)  # Skewed weights
        weights = weights / weights.sum()  # Normalize
        
        # Ensure minimum 5 samples per client per class
        min_samples = 5
        distributed = 0
        client_counts = (weights * (total_files - n_clients*min_samples)).astype(int)
        client_counts = client_counts + min_samples  # Add minimum to all
        
        # Adjust for rounding errors
        while sum(client_counts) > total_files:
            client_counts[np.argmax(client_counts)] -= 1
        
        # Distribute files
        ptr = 0
        for client_id in range(n_clients):
            count = client_counts[client_id]
            if count <= 0:
                continue
                
            client_label_dir = os.path.join(output_dir, f'client_{client_id}', str(label))
            os.makedirs(client_label_dir, exist_ok=True)
            
            for i in range(count):
                if ptr + i >= len(files):
                    break
                src_path = files[ptr + i]
                dst_path = os.path.join(client_label_dir, os.path.basename(src_path))
                shutil.copy(src_path, dst_path)
            ptr += count

    deleteAllFolder(input_dir)

if __name__ == '__main__':
    try:
        n_clients = int(sys.argv[1])
    except:
        print("Usage: python script.py <n_clients>")
        exit()

    downloadSaveData()
    split_data_non_iid_quantity("mnist_data/images", "mnist_data", n_clients)