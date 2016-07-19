import difflib

import numpy as np

from nltk.metrics import distance

class StringDistance:
    def distance(self, s1, s2):
        raise NotImplementedError

class CharacterWiseDistance(StringDistance):
    def distance(self, s1, s2):
        return np.mean([ x == y for (x, y) in zip(s1, s2) ])

class SequenceDistance(StringDistance):
    def distance(self, s1, s2):
        return difflib.SequenceMatcher(None, s1, s2).ratio()

class Levenshtein(StringDistance):
    def distance(self, s1, s2):
        ed = distance.edit_distance(s1, s2)
        if ed != 0:
            ed **= -1
            
        return 1 - ed
