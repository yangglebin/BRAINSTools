import pickle
from predict import image_data
from training import linear_array_from_image_file, train_classifier
from preprocess import save_data_frame
import pandas as pd
import os


def pickle_load(pickled_file):
    _file = open(pickled_file, "rb")
    output = pickle.load(_file)
    _file.close()
    return output


def collect_training_data(training_files):
    all_data = list()
    for t1_file, additional_files, truth_files in training_files:
        feature_data = image_data(t1_file, "T1", additional_images=additional_files)
        gm_truth_data = pd.Series(linear_array_from_image_file(truth_files["gm"]), name="GM")
        wm_truth_data = pd.Series(linear_array_from_image_file(truth_files["wm"]), name="WM")
        truth_data = pd.concat([gm_truth_data, wm_truth_data], axis=1)
        data = pd.concat([feature_data, truth_data], axis=1, keys=["Features", "Truth"])
        all_data.append(data)
    return pd.concat(all_data, axis=0)


def train_gm_classifier():
    cache_dir = "/Shared/sinapse/CACHE/20160811_Davids_MachineLearning"
    training_files = pickle_load("/Shared/sinapse/CACHE/20160811_Davids_MachineLearning/training_files.pkl")
    training_data = collect_training_data(training_files)
    training_data_file = os.path.join(cache_dir, "training_data.hdf5")
    save_data_frame(training_data, training_data_file)
    classifier_file = os.path.join(cache_dir, "Classifier", "gray_matter_classifier.pkl")
    if not os.path.isdir(os.path.dirname(classifier_file)):
        os.makedirs(os.path.dirname(classifier_file))
    train_classifier(training_data["Features"].values, training_data["Truth"]["GM"].values, classifier_file)


if __name__ == "__main__":
    train_gm_classifier()
