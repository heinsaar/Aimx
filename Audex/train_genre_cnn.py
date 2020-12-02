from pathlib import Path
from datetime import timedelta
import time
import argparse
import numpy as np
import cmd
import os

from sklearn.model_selection import train_test_split
import tensorflow.keras as keras

from audex_utils import *

# Calling with "-traindata_path /to/file" will expect to find the file in ./to directory.
parser = argparse.ArgumentParser(description = 'This utility script allows you to experiment with'
                                               ' audio files and their various spectrograms.')

parser.add_argument("-traindata_path", type = Path, help = 'Path to the data file to be fed to the NN. Or use ' + Aimx.MOST_RECENT_OUTPUT +
                                                           ', which by design is the output of the previous step of dataset preprocessing.')

parser.add_argument("-batch_size", default = 32, type=int, help = 'Batch size.')
parser.add_argument("-epochs",     default = 50, type=int, help = 'Number of epochs to train.')
parser.add_argument("-patience",   default =  5, type=int, help = 'Number of epochs with no improvement after which training will be stopped.')
parser.add_argument("-verbose",    default =  1, type=int, help = 'Verbosity modes: 0 (silent), 1 (will show progress bar),'
                                                                  ' or 2 (one line per epoch). Default is 1.')
parser.add_argument("-showplot",   action ='store_true',   help = 'At the end, will show an interactive plot of the training history.')
parser.add_argument("-savemodel",  action ='store_true',   help = 'Will save a trained model in directory ' + quote(Aimx.Paths.GEN_SAVED_MODELS))
parser.add_argument("-example",    action ='store_true',   help = 'Will show a working example on how to call the script.')

args = parser.parse_args()

########################## Command Argument Handling & Verification #######################

if args.example:
    print_info(nameofthis(__file__) + " -traindata_path most_recent_output -epochs 5")
    exit()

if provided(args.traindata_path) and not args.traindata_path.exists():
    if str(args.traindata_path) is not Aimx.MOST_RECENT_OUTPUT:
        raise FileNotFoundError("Directory " + quote(pinkred(os.getcwd())) + " does not contain requested path " + quote(pinkred(args.traindata_path)))

###########################################################################################

print_info("========================================================================================")
print_info("===========================  SCRIPT START STANDARD PREAMBLE  ===========================")
print_info("===========================  RUNNING WITH THESE PARAMETERS:  ===========================")
print_info(cyan(nameofthis(__file__)))
print_info(vars(args))
print_info("\n========================================================================================\n")

# path to the traindata file that stores MFCCs and genre labels for each processed segment
ARG_TRAINDATA_PATH = get_actual_traindata_path(args.traindata_path)

if not args.savemodel and os.path.getsize(ARG_TRAINDATA_PATH) > 100_000_000: # > 100 Mb
    args.savemodel = prompt_user_warning("Attempting to train on a large >100Mb traindata without '-savemodel',"
                                         " would you rather save the final model? [yes / no] ")
    print_info("As requested, proceeding with -savemodel =", args.savemodel)

def prepare_traindata(test_size, valid_size):
    """
    Loads data and splits it into train, validation and test sets.
    Params:
         test_size (float): Value in [0, 1] indicating percentage of dataset to allocate to test       split
        valid_size (float): Value in [0, 1] indicating percentage of dataset to allocate to validation split
    Returns:
        x_train (ndarray): Input training set
        x_valid (ndarray): Input valid set
        x_test  (ndarray): Input test set
        y_train (ndarray): Target training set
        y_valid (ndarray): Target valid set
        y_test  (ndarray): Target test set
    """
    x, y = load_traindata(ARG_TRAINDATA_PATH)

    # create train, validation and test split
    x_train, x_test,  y_train, y_test  = train_test_split(x,       y,       test_size = test_size)
    x_train, x_valid, y_train, y_valid = train_test_split(x_train, y_train, test_size = valid_size)

    # add an axis to input sets; example resulting shape: (89, 259, 13, 1)
    x_train = x_train[..., np.newaxis]
    x_valid = x_valid[..., np.newaxis]
    x_test  =  x_test[..., np.newaxis]

    print_info("Dataset view (labels) from dataprep result meta:")
    cmd.Cmd().columnize(get_dataprep_result_meta()[Aimx.Dataprep.DATASET_VIEW], displaywidth=100)

    print_info("Extended x_train (input) shape: " + str(x_train.shape))
    print_info("Extended x_valid (input) shape: " + str(x_valid.shape))
    print_info("Extended x_test  (input) shape: " + str(x_test.shape))

    return x_train, x_valid, x_test, y_train, y_valid, y_test

def build_model(input_shape):
    """
    Generates CNN model
    Param:
        input_shape (tuple): Shape of input set
    Returns:
        model: CNN model
    """
    model = keras.Sequential()

    # 1st conv layer
    model.add(keras.layers.Conv2D(filters=32, kernel_size=(3, 3), activation='relu', input_shape=input_shape))
    model.add(keras.layers.MaxPooling2D(pool_size=(3, 3), strides=(2, 2), padding='same'))
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

if __name__ == "__main__":

    # get train, validation, test splits
    x_train, x_valid, x_test, y_train, y_valid, y_test = prepare_traindata(test_size = 0.25, valid_size = 0.2)

    # create network
    model = build_model(input_shape = (x_train.shape[1], x_train.shape[2], 1))

    model.compile(optimizer = keras.optimizers.Adam(learning_rate = 0.0001),
                  loss      = 'sparse_categorical_crossentropy',
                  metrics   = ['accuracy'])

    model.summary()

    earlystop_callback = keras.callbacks.EarlyStopping(monitor="accuracy", min_delta=0.001, patience=args.patience)

    start_time = time.time()

    # train model
    history = model.fit(x_train, y_train, validation_data = (x_valid, y_valid),
                       batch_size = args.batch_size,
                       epochs     = args.epochs,
                       verbose    = args.verbose,
                       callbacks  = [earlystop_callback])

    training_duration = timedelta(seconds = round(time.time() - start_time))
    timestamp = timestamp_now()

    print_info("Finished {} at {} with wall clock time: {} ".format(cyansky(nameofthis(__file__)),
                                                                    lightyellow(timestamp),
                                                                    lightyellow(training_duration)))
    # evaluate model on test set
    test_loss, test_acc = model.evaluate(x_test, y_test, verbose = args.verbose)
    print_info('\nTest accuracy:', test_acc)
        
    # pick a sample to predict from the test set
    x_to_predict = x_test[30]
    y_to_predict = y_test[30] # target

    # predict sample
    predict(model, x_to_predict, y_to_predict)

    trainid = "cnn_e" + str(args.epochs) + "_" + extract_filename(ARG_TRAINDATA_PATH)

    # save as most recent training result metadata
    save_training_result_meta(trainid, timestamp, str(training_duration), args.savemodel)

    if (args.savemodel):
        save_model(model, trainid)
    
    plot_history(history, trainid, args.showplot) # accuracy and error as a function of epochs