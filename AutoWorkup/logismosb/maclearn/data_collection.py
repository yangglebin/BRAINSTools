from train_gm_classifier import collect_training_data, pickle_load, save_data_frame
import os


def save_training_data():
    cache_dir = "/Shared/sinapse/CACHE/20161019_Davids_CrossValidation"
    training_files = pickle_load(os.path.join(cache_dir, "training_files.pkl"))
    training_data = collect_training_data(training_files)
    training_data_file = os.path.join(cache_dir, "training_data.hdf5")
    save_data_frame(training_data, training_data_file)

if __name__ == "__main__":
    save_training_data()