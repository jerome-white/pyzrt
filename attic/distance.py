import difflib

import numpy as np

from nltk.metrics import distance

def characters(s1, s2):
    return np.mean([ x == y for (x, y) in zip(s1, s2) ])

def sequence(s1, s2):
    return difflib.SequenceMatcher(None, s1, s2).ratio()

def levenshtein(s1, s2):
    ed = distance.edit_distance(self, other)
    if ed != 0:
        ed **= -1

    return 1 - ed
