from imutils import paths
import numpy as np
import os
import cv2
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPool2D,Flatten,Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import SGD, Adam
import random

def load_data_byCid(cid, dataset='cifar10'):
    data = []
    labels = []
    
    path = f"{dataset}_data/client_{cid}"
    img_paths = list(paths.list_images(path))
    
    for imgpath in img_paths:
        # Load image based on dataset type
        if dataset == 'cifar10':
            img = cv2.imread(imgpath)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
        else:  # MNIST
            img = cv2.imread(imgpath, cv2.IMREAD_GRAYSCALE)
            img = np.expand_dims(img, axis=-1)  # Add channel dimension
            
        # Normalize and ensure float32
        img = img.astype('float32') / 255.0
        
        # Get label from folder name
        label = int(imgpath.split(os.path.sep)[-2])
        
        data.append(img)
        labels.append(label)
    
    return np.array(data), np.array(labels)

def define_model(input_shape, num_classes, dataset='cifar10'):
    model = Sequential()
    
    if dataset == 'cifar10':
        # CIFAR-10 model
        model.add(Conv2D(32, (3, 3), activation='relu', padding='same', input_shape=input_shape))
        model.add(BatchNormalization())
        model.add(Conv2D(32, (3, 3), activation='relu', padding='same'))
        model.add(BatchNormalization())
        model.add(MaxPool2D((2, 2)))
        model.add(Dropout(0.2))
        
        model.add(Conv2D(64, (3, 3), activation='relu', padding='same'))
        model.add(BatchNormalization())
        model.add(Conv2D(64, (3, 3), activation='relu', padding='same'))
        model.add(BatchNormalization())
        model.add(MaxPool2D((2, 2)))
        model.add(Dropout(0.3))
        
        model.add(Conv2D(128, (3, 3), activation='relu', padding='same'))
        model.add(BatchNormalization())
        model.add(Conv2D(128, (3, 3), activation='relu', padding='same'))
        model.add(BatchNormalization())
        model.add(MaxPool2D((2, 2)))
        model.add(Dropout(0.4))
        
        model.add(Flatten())
        model.add(Dense(128, activation='relu'))
        model.add(BatchNormalization())
        model.add(Dropout(0.5))
    else:
        # MNIST model
        model.add(Conv2D(32, (3, 3), activation='relu', input_shape=input_shape))
        model.add(MaxPool2D((2, 2)))
        model.add(Flatten())
        model.add(Dense(100, activation='relu'))
    
    model.add(Dense(num_classes, activation='softmax'))
    
    opt = Adam(learning_rate=0.001)  # Using Adam optimizer which often works better
    model.compile(optimizer=opt, loss='categorical_crossentropy', metrics=['accuracy'])
    
    return model

def setWeightSingleList(weights):
    # Flatten each array of weights into a 1D list of floats
    weights_flat = [w.flatten() for w in weights]

    # Concatenate all of the weight lists into a single list
    weights = np.concatenate(weights_flat).tolist()

    return weights

def reshapeWeight(server_weight, client_weight):
    reshape_weight = []

    # iterate through the weights in the model and reshape the corresponding sublist of the concatenated weight list
    for layer_weights in client_weight:
        n_weights = np.prod(layer_weights.shape)
        reshape_weight.append(np.array(server_weight[:n_weights]).reshape(layer_weights.shape))
        server_weight = server_weight[n_weights:]

    return reshape_weight

def createRandomClientList(clients_dictionary, n_round_clients):
    keys = list(clients_dictionary.keys())
    return random.sample(keys, n_round_clients)

def euclidean_distances(global_weight, client_weight):
    return np.sqrt(np.sum(np.square(np.subtract(global_weight, client_weight))))

def inter_quarlite_rage_limits(distances):
    q1 = np.percentile(distances, 25)
    q3 = np.percentile(distances, 75)
    iqr = q3 - q1

    return q1 - 1.5*iqr, q3 + 1.5*iqr