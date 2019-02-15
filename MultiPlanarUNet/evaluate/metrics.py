"""
Mathias Perslev
MSc Bioinformatics

University of Copenhagen
November 2017
"""

import numpy as np
import tensorflow as tf
from tensorflow.keras.utils import to_categorical


def dice(y_true, y_pred, smooth=1.0):
    """
    Calculates the Soerensen dice coefficient between two binary sets
    """
    # Flatten and bool the ground truth and predicted labels
    s1 = np.array(y_true).flatten().astype(np.bool)
    s2 = np.array(y_pred).flatten().astype(np.bool)

    # Calculate dice
    return (smooth + 2 * np.logical_and(s1, s2).sum()) \
           / (smooth + s1.sum() + s2.sum())


def dice_all(y_true, y_pred, smooth=1.0, n_classes=None, ignore_zero=True,
             skip_if_no_y=False):
    """
    Calculates the Soerensen dice coefficients for all unique classes
    """
    # Get array of unique classes in true label array
    if n_classes is None:
        classes = np.unique(y_true)
    else:
        if n_classes == 1:
            n_classes = 2
        classes = np.arange(n_classes)

    # Ignore background class?
    if ignore_zero:
        classes = classes[np.where(classes != 0)]

    # Calculate dice for all targets
    dice_coeffs = np.empty(shape=classes.shape, dtype=np.float32)
    dice_coeffs.fill(np.nan)
    for idx, _class in enumerate(classes):
        s1 = y_true == _class
        if skip_if_no_y and not np.any(s1):
            continue
        s2 = y_pred == _class

        if np.any(s1) or np.any(s2):
            d = dice(s1, s2, smooth=smooth)
            dice_coeffs[idx] = d
    return dice_coeffs


def one_class_dice(y_true, y_pred, smooth=1.0):
    # Predict
    y_pred = tf.cast(y_pred > 0.5, tf.float32)

    return (smooth + 2.0 * tf.reduce_sum(y_true * y_pred)) / (smooth + tf.reduce_sum(y_true) + tf.reduce_sum(y_pred))


def precision(y_true, y_pred):
    y_pred = tf.round(y_pred)
    not_true = tf.cast(tf.logical_not(tf.cast(y_true, tf.bool)), tf.float32)

    tp = tf.reduce_sum(tf.multiply(y_true, y_pred))
    fp = tf.reduce_sum(tf.multiply(not_true, y_pred))

    return tp / (tp+fp)


def recall(y_true, y_pred):
    y_pred = np.round(y_pred)
    tp = tf.reduce_sum(tf.multiply(y_true, y_pred))
    relevant = tf.reduce_sum(y_true)

    return tp/relevant


def sparse_fg_recall(y_true, y_pred, bg_class=0):
    # Get MAP estimates
    y_true = tf.cast(tf.reshape(y_true, [-1]), tf.int32)
    y_pred = tf.cast(tf.reshape(tf.argmax(y_pred, axis=-1), [-1]), tf.int32)

    # Remove background
    mask = tf.not_equal(y_true, bg_class)
    y_true = tf.boolean_mask(y_true, mask)
    y_pred = tf.boolean_mask(y_pred, mask)

    return tf.reduce_mean(tf.cast(tf.equal(y_true, y_pred), tf.float32))


def fg_recall(y_true, y_pred, bg_class=0):
    # Get MAP estimates
    y_true = tf.argmax(y_true, axis=-1)

    return sparse_fg_recall(y_true, y_pred, bg_class)


def sparse_mean_fg_f1(y_true, y_pred):
    y_pred = tf.argmax(y_pred, axis=-1)

    # Get confusion matrix
    cm = tf.confusion_matrix(tf.reshape(y_true, [-1]),
                             tf.reshape(y_pred, [-1]))

    # Get precisions
    TP = tf.diag_part(cm)
    precisions = TP / tf.reduce_sum(cm, axis=0)

    # Get recalls
    TP = tf.diag_part(cm)
    recalls = TP / tf.reduce_sum(cm, axis=1)

    # Get F1s
    f1s = (2 * precisions * recalls) / (precisions + recalls)

    return tf.reduce_mean(f1s[1:])


def sparse_mean_fg_precision(y_true, y_pred):
    y_pred = tf.argmax(y_pred, axis=-1)

    # Get confusion matrix
    cm = tf.confusion_matrix(tf.reshape(y_true, [-1]),
                             tf.reshape(y_pred, [-1]))

    # Get precisions
    TP = tf.diag_part(cm)
    precisions = TP / tf.reduce_sum(cm, axis=0)

    return tf.reduce_mean(precisions[1:])


def sparse_mean_fg_recall(y_true, y_pred):
    y_pred = tf.argmax(y_pred, axis=-1)

    # Get confusion matrix
    cm = tf.confusion_matrix(tf.reshape(y_true, [-1]),
                             tf.reshape(y_pred, [-1]))

    # Get precisions
    TP = tf.diag_part(cm)
    recalls = TP / tf.reduce_sum(cm, axis=1)

    return tf.reduce_mean(recalls[1:])


def sparse_fg_precision(y_true, y_pred, bg_class=0):
    # Get MAP estimates
    y_true = tf.cast(tf.reshape(y_true, [-1]), tf.int32)
    y_pred = tf.cast(tf.reshape(tf.argmax(y_pred, axis=-1), [-1]), tf.int32)

    # Remove background
    mask = tf.not_equal(y_pred, bg_class)
    y_true = tf.boolean_mask(y_true, mask)
    y_pred = tf.boolean_mask(y_pred, mask)

    return tf.reduce_mean(tf.cast(tf.equal(y_true, y_pred), tf.float32))


def fg_precision(y_true, y_pred, bg_class=0):
    # Get MAP estimates
    y_true = tf.argmax(y_true, axis=-1)

    return sparse_fg_precision(y_true, y_pred, bg_class)


def np_pr_class_entropy(target, output, n_classes):
    output = output.reshape(-1, n_classes)
    target = to_categorical(target.reshape(-1, 1), num_classes=n_classes)

    # For num. stability
    output /= np.sum(output, -1, keepdims=True)
    epsilon = 1e-7
    output = np.clip(output, epsilon, 1. - epsilon)

    return -np.mean(target * np.log(output), axis=0)
