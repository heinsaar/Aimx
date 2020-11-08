from pathlib import PurePath
from pathlib import Path
import argparse
import librosa
import numpy as np
import time
import json
import math
import os

from sklearn.model_selection import train_test_split
import tensorflow.keras as keras
from termcolor import colored

from genre_classifier import load_data
from genre_utils      import *

# Calling with "-data_path /to/file" will expect to find the file in ./to directory.
parser = argparse.ArgumentParser(description = 'This utility script allows you to experiment with'
                                               ' audio files and their various spectrograms.')

parser.add_argument("-data_path", type = Path, help = 'Path to the data file to be fed to the NN. Or use "most_recent_output", which'
                                                      ' by design is the output of the previous step of dataset preprocessing.')
parser.add_argument("-batch_size", default = 32, type=int, help = 'Batch size.')
parser.add_argument("-epochs",     default = 50, type=int, help = 'Number of epochs to train.')
parser.add_argument("-verbose",    default =  1, type=int, help = 'Verbosity modes: 0 (silent), 1 (will show progress bar),'
                                                                  ' or 2 (one line per epoch). Default is 1.')
parser.add_argument("-noplot",     action ='store_true',   help = 'Will not show any plots (useful for certain test automation).')

args = parser.parse_args()

############################## Command Argument Verification ##############################

if provided(args.data_path) and not args.data_path.exists():
    if str(args.data_path) is not "most_recent_output":
        raise FileNotFoundError("Directory " + quote(pinkred(os.getcwd())) + " does not contain requested path " + quote(pinkred(args.data_path)))

###########################################################################################

# path to json file that stores MFCCs and genre labels for each processed segment
ARG_DATA_PATH = args.data_path if provided(args.data_path) else ""
if str(ARG_DATA_PATH) == "most_recent_output":
    ARG_DATA_PATH = get_preprocess_result_meta()["most_recent_output"]

def prepare_datasets(test_size, valid_size):
    """Loads data and splits it into train, validation and test sets.
    :param  test_size (float): Value in [0, 1] indicating percentage of dataset to allocate to test split
    :param valid_size (float): Value in [0, 1] indicating percentage of dataset to allocate to validation split
    :return x_train (ndarray): Input training set
    :return x_valid (ndarray): Input valid set
    :return x_test  (ndarray): Input test set
    :return y_train (ndarray): Target training set
    :return y_valid (ndarray): Target valid set
    :return y_test  (ndarray): Target test set
    """
    x, y = load_data(ARG_DATA_PATH)

    # create train, validation and test split
    x_train, x_test,  y_train, y_test  = train_test_split(x,       y,       test_size = test_size)
    x_train, x_valid, y_train, y_valid = train_test_split(x_train, y_train, test_size = valid_size)

    print(pinkred(x_train.shape))
    # add an axis to input sets
    x_train = x_train[..., np.newaxis]
    print(red(x_train.shape))
    exit()
    x_valid = x_valid[..., np.newaxis]
    x_test  = x_test[ ..., np.newaxis]

    return x_train, x_valid, x_test, y_train, y_valid, y_test

def build_model(input_shape):
    """Generates CNN model
    :param input_shape (tuple): Shape of input set
    :return model: CNN model
    """
    model = keras.Sequential()

    # 1st conv layer
    model.add(keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=input_shape))
    model.add(keras.layers.MaxPooling2D((3, 3), strides=(2, 2), padding='same'))
    model.add(keras.layers.BatchNormalization())

    # 2nd conv layer
    model.add(keras.layers.Conv2D(32, (3, 3), activation='relu'))
    model.add(keras.layers.MaxPooling2D((3, 3), strides=(2, 2), padding='same'))
    model.add(keras.layers.BatchNormalization())

    # 3rd conv layer
    model.add(keras.layers.Conv2D(32, (2, 2), activation='relu'))
    model.add(keras.layers.MaxPooling2D((2, 2), strides=(2, 2), padding='same'))
    model.add(keras.layers.BatchNormalization())

    # flatten output and feed it into dense layer
    model.add(keras.layers.Flatten())
    model.add(keras.layers.Dense(64, activation='relu'))
    model.add(keras.layers.Dropout(0.3))

    # output layer
    model.add(keras.layers.Dense(10, activation='softmax'))

    return model


def predict(model, X, y):
    """Predict a single sample using the trained model
    :param model: Trained classifier
    :param X: Input data
    :param y (int): Target
    """

    # add a dimension to input data for sample - model.predict() expects a 4d array in this case
    X = X[np.newaxis, ...] # array shape (1, 130, 13, 1)

    # perform prediction
    prediction = model.predict(X)

    # get index with max value
    predicted_index = np.argmax(prediction, axis=1)

    print("Target: {}, Predicted label: {}".format(y, predicted_index))

if __name__ == "__main__":

    # get train, validation, test splits
    x_train, x_valid, x_test, y_train, y_valid, y_test = prepare_datasets(0.25, 0.2)

    # create network
    model = build_model(input_shape = (x_train.shape[1], x_train.shape[2], 1))

    model.compile(optimizer = keras.optimizers.Adam(learning_rate = 0.0001),
                  loss      = 'sparse_categorical_crossentropy',
                  metrics   = ['accuracy'])

    model.summary()

    # train model
    history = model.fit(x_train, y_train, validation_data = (x_valid, y_valid), batch_size=args.batch_size, epochs=args.epochs)

    # plot accuracy/error for training and validation
    plot_history(history)

    # evaluate model on test set
    test_loss, test_acc = model.evaluate(x_test, y_test, verbose=2)
    print('\nTest accuracy:', test_acc)

    # pick a sample to predict from the test set
    x_to_predict = x_test[30]
    y_to_predict = y_test[30]

    # predict sample
    predict(model, x_to_predict, y_to_predict)