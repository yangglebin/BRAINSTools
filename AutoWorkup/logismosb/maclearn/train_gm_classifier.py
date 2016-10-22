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


def get_subject_id_from_t1(t1_file):
    return os.path.abspath(t1_file).split("/")[-3]


def collect_training_data(training_files):
    all_data = list()
    for t1_file, additional_files, truth_files in training_files:
        feature_data = image_data(t1_file, "T1", additional_images=additional_files)
        subject_id = get_subject_id_from_t1(t1_file)
        print(subject_id)
        index = pd.MultiIndex.from_tuples([(subject_id, i) for i in feature_data.index])
        gm_truth_data = pd.Series(linear_array_from_image_file(truth_files["gm"]), name="GM", index=index)
        wm_truth_data = pd.Series(linear_array_from_image_file(truth_files["wm"]), name="WM", index=index)
        truth_data = pd.concat([gm_truth_data, wm_truth_data], axis=1)
        data = pd.concat([feature_data, truth_data], axis=1, keys=["Features", "Truth"])
        all_data.append(data)
    return pd.concat(all_data, axis=0)


def train_gm_classifier(cache_dir):
    classifier_file = os.path.join(cache_dir, "Classifier", "gray_matter_classifier.pkl")
    if not os.path.isdir(os.path.dirname(classifier_file)):
        os.makedirs(os.path.dirname(classifier_file))
    train_classifier(training_data["Features"].values, training_data["Truth"]["GM"].values, classifier_file)


if __name__ == "__main__":
    train_gm_classifier(os.path.curdir)
