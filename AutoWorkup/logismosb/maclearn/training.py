import sklearn
import numpy
import os
import csv
import sys
import random
import ast
import SimpleITK as sitk
from sklearn.externals import joblib
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import json


def get_list_of_features():
    _file = open("data_order.json", "rb")
    features = json.load(_file)
    _file.close()
    return features


def remove_keys_from_array(array, keys):
    for key in keys:
        array.remove(key)
    return array


def mask_with_abc_image(image, abc_image):
    abc_mask = get_brainmask(abc_image)
    masked_image = sitk.Mask(image, abc_mask)
    return masked_image


def binary_close(image, amount=1):
    image = sitk.BinaryErode(image, amount)
    image = sitk.BinaryDilate(image, amount)
    return image


def get_brainmask(abc_image):
    exclude_image = abc_image < 0
    exclude_codes = [5, 11, 12, 30]
    for code in exclude_codes:
        exclude_image = exclude_image + (abc_image == code)
    exclude_image = binary_close(exclude_image, 2)
    brainmask = abc_image * (exclude_image == 0) > 0

    return brainmask


def masked_image_array(image, mask):
    return imagearray(sitk.Mask(image, mask))


def mask_array_with_image(array, mask_image):
    mask_array = imagearray(mask_image)
    array[numpy.where(mask_array == 0)] = 0
    return array


def mask_data_with_image(data, mask_image):
    for i, array in enumerate(data):
        data[i] = mask_array_with_image(array, mask_image)
    return data


def linear_array_from_image_file(image_file):
    image = sitk.ReadImage(image_file)
    return imagearray(image)


def imagearray(image):
    """returns the 1D array of the numpy matrix"""
    a = sitk.GetArrayFromImage(image)
    a1D = a.reshape(a.size)
    return a1D


def databyregion(data, wmtargets, wmlabelmap, wmlabels, gmtargets, gmlabelmap, gmlabels):
    """
    Takes in an label map image and devides the data and
    targets into specified regions. Regoins are specified
    by a label list.
    """
    columns = [data]
    keys = ['Features', 'WMRegions', 'GMRegions', 'Targets']

    wmregions = list()
    for i, label in enumerate(wmlabels):
        wmregions.append(pd.Series(wmlabelmap == label))
    df_wm = pd.concat(wmregions, axis=1, keys=wmlabels)

    gmregions = list()
    for i, label in enumerate(gmlabels):
        gmregions.append(pd.Series(gmlabelmap == label))
    df_gm = pd.concat(gmregions, axis=1, keys=gmlabels)

    df_targets = pd.concat([pd.Series(wmtargets), pd.Series(gmtargets)], axis=1, keys=['WM', 'GM'])

    df = pd.concat([data, df_wm, df_gm, df_targets], axis=1, keys=keys)

    return df


def image_data(in_file, modality, abc_file=None, additional_images=None):
    """
    Computes the image features to be used for edge detection. Features are
    returned as a Pandas DataFrame.

    inputs:
        in_file : image file to be read in by SimpleITK
        modlaity : name of the modality
    outputs:
        data : dataframe object containing the image metrics
    """

    # features can be added or taken out as to optimize the edge detection
    features = get_list_of_features()

    image = sitk.ReadImage(in_file)
    intensity_values = imagearray(image)

    grad = sitk.GradientMagnitude(image)
    grad_values = imagearray(grad)
    sigmas = [i * .5 for i in range(1, 5)]
    gauss_gradients = [imagearray(sitk.GradientMagnitudeRecursiveGaussian(image, sigma=sigma)) for sigma in sigmas]
    gauss_gradient_names = ["GaussGrad_{0:.1f}".format(sigma).replace('.', '_') for sigma in sigmas]

    grad_2 = sitk.GradientMagnitude(grad)
    grad_2_values = imagearray(grad_2)

    lap_values = imagearray(sitk.Laplacian(sitk.Cast(image, sitk.sitkFloat32)))
    gauss_lap = imagearray(sitk.LaplacianRecursiveGaussian(image))
    sobel_values = imagearray(sitk.SobelEdgeDetection(sitk.Cast(image, sitk.sitkFloat32)))

    directional_gradients = list(getgradientinfo(image))
    directional_gradient_names = ["GradX", "GradY", "GradZ", "Eigen1", "Eigen2", "Eigen3"]

    gauss_image = sitk.SmoothingRecursiveGaussian(image, sigma=1.0)
    gauss_array = imagearray(gauss_image)
    gauss_directional_gradients = list(getgradientinfo(gauss_image))
    gauss_directional_gradient_names = ["Gauss_" + name for name in directional_gradient_names]

    array_list = [intensity_values, gauss_array, grad_values, grad_2_values, lap_values, gauss_lap,
                  sobel_values] + gauss_gradients + directional_gradients + gauss_directional_gradients

    if abc_file:
        abc_image = sitk.ReadImage(abc_file)
        mask_image = get_brainmask(abc_image)
        array_list = mask_data_with_image(array_list, mask_image)

    series_list = [pd.Series(array) for array in array_list]
    keys = [modality + meas for meas in ['', 'Smoothed', 'GradMag', 'GradMag2', 'Laplacian', 'LapGauss',
                                         'Sobel'] + gauss_gradient_names + directional_gradient_names + gauss_directional_gradient_names]

    features = remove_keys_from_array(features, keys)

    for name in features:
        series_list.append(pd.Series(imagearray(sitk.ReadImage(additional_images[name]))))
        keys.append(name)

    data = pd.concat(series_list,
                     keys=keys,
                     axis=1)

    return data


def getgradientinfo(t1):
    """
    Takes in an image and computes the gradient, and hessian and returns
    the eigen values of the hessian.
    """
    grad = sitk.Gradient(t1)

    g_array = sitk.GetArrayFromImage(grad)

    gx = sitk.GetImageFromArray(g_array[:, :, :, 0])
    gy = sitk.GetImageFromArray(g_array[:, :, :, 1])
    gz = sitk.GetImageFromArray(g_array[:, :, :, 2])

    for img in [gx, gy, gz]:
        img.SetDirection(t1.GetDirection())
        img.SetOrigin(t1.GetOrigin())
        img.SetSpacing(t1.GetSpacing())

    ggx = sitk.Gradient(gx)
    ggy = sitk.Gradient(gy)
    ggz = sitk.Gradient(gz)

    ggx_array = sitk.GetArrayFromImage(ggx)
    ggy_array = sitk.GetArrayFromImage(ggy)
    ggz_array = sitk.GetArrayFromImage(ggz)

    hessian = numpy.stack((ggx_array, ggy_array, ggz_array), axis=3)
    eigvals = numpy.linalg.eigvals(hessian[:, :, :, :, :])

    gx_array = numpy.abs(numpy.ravel(g_array[:, :, :, 0]))
    gy_array = numpy.abs(numpy.ravel(g_array[:, :, :, 1]))
    gz_array = numpy.abs(numpy.ravel(g_array[:, :, :, 2]))

    eigen1 = numpy.ravel(eigvals[:, :, :, 0])
    eigen2 = numpy.ravel(eigvals[:, :, :, 1])
    eigen3 = numpy.ravel(eigvals[:, :, :, 2])

    return gx_array, gy_array, gz_array, eigen1, eigen2, eigen3


def multimodalimagedata(sample_dict):
    """Collects and Combines the image data from multiple modalities"""
    modals = sample_dict["Modalities"]
    if len(modals) > 1:
        data_list = list()
        for j, modal in enumerate(modals): # iterate through the modalities
            data_list.append(image_data(sample_dict[modal], modal))
        df = pd.concat(data_list, axis=1)
    else:
        df = image_data(sample_dict[modals[0]], modals[0])
    return df


def collectdata(data_csv):
    """
    Collects the training data from a csv file.
    CSV header format must contain 'Truth', 'Labelmap', 'Labels', and
    'Modalities'.
    """

    data_samples = list()
    with open(data_csv, "rb") as csvfile:
        reader = csv.DictReader(csvfile)
        for i, line in enumerate(reader):
            try:

                if i == 0:
                    modalities = ast.literal_eval(line["Modalities"])
                    gmlabels = ast.literal_eval(line["GMLabels"])
                    wmlabels = ast.literal_eval(line["WMLabels"])
                else:
                    # check that the modalities and labels remain constant
                    if not modalities == ast.literal_eval(line["Modalities"]):
                        print("ERROR: csv line %d - Modalities must be the same for all subjects" % i)
                    elif not gmlabels == ast.literal_eval(line["GMLabels"]):
                        print("ERROR: csv line %d - GMLabels must be the same for all subjects" % i)
                    elif not wmlabels == ast.literal_eval(line["WMLabels"]):
                        print("ERROR: csv line %d - WMLabels must be the same for all subjects" % i)

                # replace the string representations with the literal representations
                line["Modalities"] = modalities
                line["GMLabels"] = gmlabels
                line["WMLabels"] = wmlabels

                data_samples.append(line)

            except KeyError, e:
                print("ERROR: csv line {0} KeyError: {1}".format(i + 1, str(e)))
                sys.exit()

    return data_samples


def splitdata(data_samples, per_testing=.1):
    """
    Split the data samples into training and testing sets.
    """

    if per_testing < 0 or per_testing > 1:
        print("ERROR: Testing percentage must be between 0 and 1")
        sys.exit()

    n = len(data_samples)
    n_test = int(n * per_testing) # will always round down

    # randomly shuffle the training samples
    train_samples = data_samples
    random.shuffle(data_samples)
    test_samples = list()
    while len(train_samples) > n - n_test:
        test_samples.append(train_samples.pop())

    return train_samples, test_samples


def combinedata(data_samples):
    """
    Takes the given data samples, reads in the images, and combines
    the image data and the targets to be used for classifier
    training.
    """

    df_list = list()
    id_list = list()

    for line in data_samples:
        # collect new data
        id_list.append(line['ID'])
        new_data = multimodalimagedata(line)

        # read in the target data
        gm_targets = imagearray(sitk.ReadImage(line["GMEdges"]))
        wm_targets = imagearray(sitk.ReadImage(line["WMEdges"]))

        # read in the label map
        wmlabelmap = imagearray(sitk.ReadImage(line["WMLabelmap"]))
        wmlabels = line["WMLabels"]

        # read in the label map
        gmlabelmap = imagearray(sitk.ReadImage(line["GMLabelmap"]))
        gmlabels = line["GMLabels"]

        # split the data by the labeled regions
        df_list.append(databyregion(new_data,
                                    wm_targets, wmlabelmap, wmlabels,
                                    gm_targets, gmlabelmap, gmlabels))

    df_final = pd.concat(df_list, axis=0, keys=id_list)

    return df_final


def get_labeled_region_data(t_data, rg_name, label, matter):
    # Training
    t_index = t_data[rg_name][label]
    t_targets = t_data['Targets'][matter][t_index].values
    t_feat = t_data['Features'][t_index].values

    return t_feat, t_targets


def train_classifier(data, targets, out_file, clf=RandomForestClassifier(), n_jobs=-1, load_clf=True):
    """Trains the classifier and dumps the pickle file"""
    if os.path.isfile(out_file):
        print("Found classifier {0}".format(out_file))
        if not load_clf:
            return
        clf = joblib.load(out_file)
    else:
        print("Fitting classifier {0}".format(out_file))
        clf.n_jobs = n_jobs
        clf.fit(data, targets)
        joblib.dump(clf, out_file)
    return clf


def run_training(training_data, train_base_clf=False, out_dir=".", n_jobs=-1):
    all_training_features = training_data['Features'].values
    classifiers = dict()
    for matter in ['WM', 'GM']:
        classifiers[matter] = dict()

        print("Training {0}".format(matter))
        # Get WM training targets
        train_matter_targets = training_data['Targets'][matter].values

        if train_base_clf:
            base_clf_file = os.path.join(out_dir, "{0}BaseCLF.pkl".format(matter))
            train_classifier(all_training_features, train_matter_targets, base_clf_file, n_jobs=n_jobs, load_clf=False)
            classifiers[matter]['NonRegional'] = base_clf_file

        rg_name = matter + 'Regions'

        classifiers[matter]['Regional'] = dict()

        for label in training_data[rg_name].columns:

            # get label specific data
            label_train_features, label_train_targets = get_labeled_region_data(training_data, rg_name, label, matter)

            # train regional classifier
            regional_clf_file = os.path.join(out_dir, "{0}{1}RegionalCLF.pkl".format(matter, label))
            train_classifier(label_train_features, label_train_targets, regional_clf_file, n_jobs=n_jobs,
                             load_clf=False)

            classifiers[matter]['Regional'][label] = regional_clf_file

    return classifiers
