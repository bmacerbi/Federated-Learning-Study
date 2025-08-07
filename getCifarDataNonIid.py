import os
import shutil
import random
import sys
import numpy as np
from PIL import Image
from tensorflow.keras.datasets import cifar10

def deleteAllFolder(path):
    for file_name in os.listdir(path):
        file_path = os.path.join(path, file_name)
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)

def downloadSaveData():
    (train_images, train_labels), (_, _) = cifar10.load_data()
    
    data_dir = 'cifar10_data'  

    if os.path.exists(data_dir):
        deleteAllFolder(data_dir)
    else:
        os.makedirs(data_dir)

    out_dir = 'cifar10_data/images' 

    for i, (img, label) in enumerate(zip(train_images, train_labels)):
        img = Image.fromarray(img)  
        label = label[0]  
        label_dir = os.path.join(out_dir, str(label))
        os.makedirs(label_dir, exist_ok=True)
        img.save(os.path.join(label_dir, f'{i}.jpg'))

def split_data_non_iid_min_one(input_dir, output_dir, n_clients):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # First create all client directories
    for i in range(n_clients):
        client_dir = os.path.join(output_dir, f'client_{i}')
        os.makedirs(client_dir, exist_ok=True)
        for label in range(10):
            os.makedirs(os.path.join(client_dir, str(label)), exist_ok=True)

    # For each class, distribute images unevenly but ensure each client gets at least one
    for label in range(10):
        file_names = os.listdir(os.path.join(input_dir, str(label)))
        random.shuffle(file_names)
        total_files = len(file_names)
        
        # First assign one sample to each client
        assigned = [1 for _ in range(n_clients)]
        remaining_files = total_files - n_clients
        
        if remaining_files > 0:
            # Generate random proportions for remaining files
            proportions = np.random.dirichlet(np.ones(n_clients) * 0.5, size=1)[0]  # More skewed with 0.5
            
            # Distribute remaining files according to proportions
            prop_sum = sum(proportions)
            for client in range(n_clients):
                additional = int(round(proportions[client] / prop_sum * remaining_files))
                assigned[client] += additional
        
        # Ensure we didn't overallocate
        while sum(assigned) > total_files:
            assigned[np.argmax(assigned)] -= 1
        
        # Distribute files
        start_idx = 0
        for client_idx in range(n_clients):
            end_idx = start_idx + assigned[client_idx]
            client_files = file_names[start_idx:end_idx]
            
            for file_name in client_files:
                src_path = os.path.join(input_dir, str(label), file_name)
                dst_path = os.path.join(output_dir, f'client_{client_idx}', str(label), file_name)
                shutil.copy(src_path, dst_path)
            
            start_idx = end_idx

    deleteAllFolder(input_dir)

if __name__ == '__main__':
    try:
        n_clients = int(sys.argv[1])
    except IndexError:
        print("Missing argument! Number of clients...")
        exit()

    downloadSaveData()
    split_data_non_iid_min_one("cifar10_data/images", "cifar10_data", n_clients)