from pathlib import Path

import json
import os

import matplotlib.pyplot as pt

from common_utils import *

DATA_PREPROCESS_RESULT_METADATA_FILENAME = "preprocess_result_meta.json"

def get_recent_preprocess_result_metadata():
    with open(DATA_PREPROCESS_RESULT_METADATA_FILENAME, "r") as file:
        print_info("\n|||||| Loading file " + cyansky(DATA_PREPROCESS_RESULT_METADATA_FILENAME) + "...", end="")
        preprocess_result_metadata = json.load(file)
        print_info(" [DONE]")
    return preprocess_result_metadata

def plot_history(history):
    """ Plots accuracy/loss for training/validation set as a function of epochs
        :param history: Training history of model
    """
    fig, axs = pt.subplots(2, figsize=(8, 6))
    dataset_json_filename = get_recent_preprocess_result_metadata()["most_recent_output"]
    fig.canvas.set_window_title("Accuracy & Error - " + get_dataset_code(dataset_json_filename))

    # create accuracy sublpot
    axs[0].plot(history.history["accuracy"],     label="train")
    axs[0].plot(history.history["val_accuracy"], label="test")
    axs[0].set_ylabel("Accuracy")
    axs[0].legend(loc="lower right")

    # create error sublpot
    axs[1].plot(history.history["loss"],     label="train")
    axs[1].plot(history.history["val_loss"], label="test")
    axs[1].set_ylabel("Error")
    axs[1].set_xlabel("Epoch")
    axs[1].legend(loc="upper right")

    pt.show()