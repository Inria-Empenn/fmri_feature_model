import csv
import os

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
from numpy import loadtxt

import matplotlib
import matplotlib as mpl

import hashlib

from numpy import corrcoef, reshape, nan, isnan
from scipy.stats import spearmanr
from nibabel import load, Nifti1Image
from nibabel.processing import resample_from_to

results_dir = os.path.abspath('/home/ymerel/fmri-feature-model/results')

def write_mean_image():
    runs = next(os.walk(results_dir))[1]

    matrices = []
    header = None
    affine = None
    for run in runs:
        img = nib.load(os.path.join(results_dir, run, "_subject_id_01", "swarsub-01_task-auditory_bold.nii"))
        matrices.append(img.get_fdata())
        if not header:
            header = img.header.copy()
            affine = img.affine
    mean = nib.Nifti1Image(np.average(matrices, axis=0), affine, header)
    nib.save(mean, os.path.join(results_dir, "mean_swarsub-01_task-auditory_bold.nii"))


def mask_using_zeros(data_image: Nifti1Image) -> Nifti1Image:
    """ Mask an image by replacing NaNs with zeros.

        Arguments:
            - data_image, nibabel.Nifti1Image : the image to mask

        Returns:
            - the masked image as nibabel.Nifti1Image
    """

    # Get data from the image
    data = data_image.get_fdata()

    # Replace NaNs by zeros
    data[isnan(data)] = 0.0

    # Return data as an image
    return Nifti1Image(data, data_image.affine)


def get_correlation_coefficient(
        file_1: str, file_2: str, method: str = 'pearson') -> float:
    """ Return the correlation coefficient of two images.

        Arguments :
            - file_1, str - path to the first image
            - file_2, str - path to the second image ; file_2 will be resampled on file_1
            - method, str - either 'pearson', or 'spearman': the correlation method to use
            - reslice_on_file_2, bool - set to :
                - True if you wish to reslice file_1 on file_2
                - False otherwise

        Returns :
            - _, float - the correlation coefficient of the two input images,
            using the passed method
    """

    # Load images
    image_1 = load(file_1)
    image_2 = load(file_2)

    # Set masking using NaN's
    image_1 = mask_using_zeros(image_1)
    image_2 = mask_using_zeros(image_2)

    # Resample using nearest neighbours
    image_2 = resample_from_to(image_2, image_1, order=0)

    # Make 1D vectors from the images data
    data_1 = reshape(image_1.get_fdata(), -1)
    data_2 = reshape(image_2.get_fdata(), -1)

    # Compute the correlation coefficient
    if method == 'pearson':
        return corrcoef(data_1, data_2)[0][1]
    if method == 'spearman':
        return spearmanr(data_1, data_2).correlation

    raise AttributeError(f'Wrong correlation method provided: {method}.')

def write_correlations(runs):
    for runx in runs:
        line = []
        for runy in runs:
            if runy == runx:
                line.append(1.0)
            else:
                print(runx + ' x ' + runy)
                line.append(get_correlation_coefficient(
                    os.path.join(results_dir, runx, '_subject_id_01', 'swarsub-01_task-auditory_bold.nii'),
                    os.path.join(results_dir, runy, '_subject_id_01', 'swarsub-01_task-auditory_bold.nii'),
                    'pearson'))
        correlations.append(line)

    matrix = np.array(correlations)
    with open(os.path.join(results_dir, 'correlations.csv'), 'w') as f:
        csv.writer(f, delimiter=' ').writerows(correlations)
    return matrix

def get_correlations_from_mean(runs):
    mean = os.path.join(results_dir, "mean_swarsub-01_task-auditory_bold.nii")
    correlations = []
    for run in runs:
        print(mean + ' x ' + run)
        correlations.append(get_correlation_coefficient(mean,
            os.path.join(results_dir, run, '_subject_id_01', 'swarsub-01_task-auditory_bold.nii'),
            'pearson'))
    return correlations


if __name__ == '__main__':

    if not os.path.exists(os.path.join(results_dir, "mean_swarsub-01_task-auditory_bold.nii")):
        write_mean_image()

    runs = next(os.walk(results_dir))[1]

    labels = []
    for run in runs:
        labels.append(run[9:])

    print(get_correlations_from_mean(runs))

    correlations = []

    if not os.path.exists(os.path.join(results_dir, 'correlations.csv')):
        matrix = write_correlations(runs)
    else:
        with open(os.path.exists(os.path.join(results_dir, 'correlations.csv')), newline='') as csvfile:
            matrix = loadtxt(os.path.join(results_dir, 'correlations.csv'), comments="#", delimiter=" ", unpack=False)

    matplotlib.use('TkAgg')
    fig, ax = plt.subplots()

    # Show all ticks and label them with the respective list entries
    ax.set_xticks(range(len(runs)), labels=labels)
    ax.set_yticks(range(len(runs)), labels=labels)
    im = ax.imshow(matrix, interpolation='nearest')

    # Loop over data dimensions and create text annotations.
    for i in range(len(runs)):
        for j in range(len(runs)):
            text = ax.text(j, i, matrix[i, j], ha="center", va="center", color="w")

    ax.set_title("Pearson correlation")
    fig.tight_layout()
    plt.show()

