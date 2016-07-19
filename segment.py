import difflib
from nltk.metrics import distance

class Sample:
    def __init__(self, data):
        self.data = data

    def __sub__(self, other):
        return np.mean([ x == y for (x, y) in zip(self.data, other.data) ])

    def __str__(self):
        return self.data

class Sequence(Sample):
    def __sub__(self, other):
        return difflib.SequenceMatcher(None, self.data, other.data).ratio()

class Levenshtein(Sample):
    def __sub__(self, other):
        ed = distance.edit_distance(self.data, other.data)
        if ed != 0:
            ed **= -1
            
        return 1 - ed
    
class Sampler(list):
    def __init__(self, data, rate=1, s=Sample):
        for i in range(0, len(data), rate):
            self.append(s(data[i:i + rate]))
