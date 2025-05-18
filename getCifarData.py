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

def split_data(input_dir, output_dir, n_clients):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for label in range(10):  
        file_names = os.listdir(os.path.join(input_dir, str(label)))
        
        random.shuffle(file_names)
        
        num_files_per_partition = len(file_names) // n_clients
        
        for i in range(n_clients):
            start_index = i * num_files_per_partition
            end_index = start_index + num_files_per_partition
            
            if i == n_clients - 1:
                end_index = len(file_names)

            if label == 0:
                client_dir = os.path.join(output_dir, f'client_{i}')
                os.makedirs(client_dir, exist_ok=True)

            client_dir_label = os.path.join(output_dir, f'client_{i}/{label}')
            os.makedirs(client_dir_label, exist_ok=True)
            
            for file_name in file_names[start_index:end_index]:
                src_path = os.path.join(input_dir, str(label), file_name)
                dst_path = os.path.join(client_dir_label, file_name)
                shutil.copy(src_path, dst_path)

    deleteAllFolder(input_dir)

if __name__ == '__main__':
    try:
        n_clients = int(sys.argv[1])
    except IOError:
        print("Missing argument! Number of clients...")
        exit()

    downloadSaveData()
    split_data("cifar10_data/images", "cifar10_data", n_clients) 