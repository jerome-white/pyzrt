import difflib

import numpy as np

from nltk.metrics import distance

class DistanceString:
    def __init__(self, data):
        self.data = data
        
    def __sub__(self, other):
        raise NotImplementedError

class CharacterWiseDistance(DistanceString):
    def __sub__(self, other):
        return np.mean([ x == y for (x, y) in zip(self.data, other.data) ])

class SequenceDistance(DistanceString):
    def __sub__(self, other):
        seq = difflib.SequenceMatcher(None, self.data, other.data)
        return seq.ratio()

class Levenshtein(DistanceString):
    def __sub__(self, other):
        ed = distance.edit_distance(self.data, other.data)
        if ed != 0:
            ed **= -1
            
        return 1 - ed
