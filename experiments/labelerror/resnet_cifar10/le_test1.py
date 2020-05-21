"""
le_test1 --> initial tests for using fiftyone with this code
This test just loads the dataset into fiftyone and exists.
It times the loading, etc...

| Copyright 2017-2020, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""
import argparse
from functools import partial
import json
import os
import random
import sys
import time

from scipy.misc import imsave
from scipy.stats import entropy

import fiftyone as fo
from fiftyone.core.odm import drop_database

from config import *
from datasets import *
from simple_resnet import *
from utils import Timer


TEMP_TRAIN_DIR = "/tmp/le_test1/train"
TEMP_VALID_DIR = "/tmp/le_test1/valid"

localtime = lambda: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def write_images(root, images, overwrite=False):
    paths = []
    for i, s in enumerate(images):
        path = os.path.join(root, f"{i:05d}.jpg")
        paths.append(path)

        if overwrite or not os.path.exists(path):
            img = s.copy()
            img = transpose(img, source="CHW", target="HWC")
            imsave(path, img)

    return paths


def main():
    #
    # Load dataset
    #
    # `train_set` and `valid_set` that are lists of `(image, label)` tuples
    #

    timer = Timer()
    whole_dataset = cifar10(root=DATA_DIR)
    print("Preprocessing training data")
    transforms = [
        partial(
            normalise,
            mean=np.array(cifar10_mean, dtype=np.float32),
            std=np.array(cifar10_std, dtype=np.float32),
        ),
        partial(transpose, source="NHWC", target="NCHW"),
    ]
    whole_train_set = list(
        zip(
            *preprocess(
                whole_dataset["train"], [partial(pad, border=4)] + transforms
            ).values()
        )
    )
    valid_set = list(
        zip(*preprocess(whole_dataset["valid"], transforms).values())
    )
    print(f"Finished loading and preprocessing in {timer():.2f} seconds")

    print(f"train set: {len(whole_train_set)} samples")
    print(f"valid set: {len(valid_set)} samples")

    # Write raw dataset to disk
    os.makedirs(TEMP_TRAIN_DIR, exist_ok=True)
    os.makedirs(TEMP_VALID_DIR, exist_ok=True)
    train_image_paths = write_images(
        TEMP_TRAIN_DIR, list(zip(*whole_train_set))[0]
    )
    valid_image_paths = write_images(TEMP_VALID_DIR, list(zip(*valid_set))[0])

    #
    # Load data into FiftyOne
    #

    timer = Timer()

    dataset = fo.Dataset("le_cifar10")

    # Train split
    train_samples = []
    for i, s in enumerate(whole_train_set):
        train_samples.append(
            fo.Sample(
                train_image_paths[i],
                tags=["train"],
                ground_truth=fo.Classification(label=cifar10_classes[s[1]]),
            )
        )

    dataset.add_samples(train_samples)

    # Val split
    val_samples = []
    for i, s in enumerate(valid_set):
        val_samples.append(
            fo.Sample(
                valid_image_paths[i],
                tags=["val"],
                ground_truth=fo.Classification(label=cifar10_classes[s[1]]),
            )
        )

    dataset.add_samples(val_samples)

    print(f"Finished getting data into fiftyone in {timer():.2f} seconds")
    print(dataset.summary())


if __name__ == "__main__":
    main()
