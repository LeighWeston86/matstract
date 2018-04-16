import itertools
import numpy as np
import matplotlib.pyplot as plt
from gensim.utils import deaccent


def plot_matrix(cm, classes,
                normalize=False,
                show_axis_labels=False,
                title='Confusion matrix',
                cmap=plt.cm.Blues):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    fmt = '.2f' if normalize else '.1f'
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    if show_axis_labels:
        plt.ylabel('True label')
        plt.xlabel('Predicted label')


def is_number(t):
    try:
        float(t.replace(',', ''))
        return True
    except ValueError:
        return False


def process_sentence(s, elements):
    for i, tok in enumerate(s):
        # write a script to split <nUm>UNIT tokens
        if is_number(tok):
            tok = "<nUm>"  # replace all numbers with a string <nUm>
        elif (len(tok) == 1 or (len(tok) > 1 and tok[0].isupper() and tok[1:].islower())) \
                and tok not in elements:
            tok = deaccent(tok.lower())  # if only first letter uppercase but not an element
        else:
            tok = deaccent(tok)
        s[i] = tok
    return s
