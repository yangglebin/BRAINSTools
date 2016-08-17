from train_gm_classifier import collect_training_data, pickle_load, train_classifier, save_data_frame
import os


def train_wm_classifier():
    cache_dir = "/Shared/sinapse/CACHE/20160811_Davids_MachineLearning"
    training_files = pickle_load("/Shared/sinapse/CACHE/20160811_Davids_MachineLearning/training_files.pkl")
    training_data = collect_training_data(training_files)
    training_data_file = os.path.join(cache_dir, "training_data.hdf5")
    save_data_frame(training_data, training_data_file)
    classifier_file = os.path.join(cache_dir, "Classifier", "white_matter_classifier.pkl")
    if not os.path.isdir(os.path.dirname(classifier_file)):
        os.makedirs(os.path.dirname(classifier_file))
    train_classifier(training_data["Features"].values, training_data["Truth"]["WM"].values, classifier_file)


if __name__ == "__train_wm_classifier__":
    train_wm_classifier()