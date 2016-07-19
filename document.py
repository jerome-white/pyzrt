import difflib

import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from lib import logger
from itertools import combinations
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
    
class Document:
    def __init__(self, fname, docno, data):
        self.fname = fname
        self.docno = docno
        self.data = data

class Corpus(list):
    def __str__(self):
        return ' '.join([ x.data for x in self ])

    def similarity(self): #, sampler):
        while True:
            words = Sampler(str(self), 1000, Sequence)
            print(len(self), len(words))
            try:
                shape = [ len(words) ] * 2
                dot = np.ones(shape, dtype=np.float16)
                break
            except MemoryError:
                cull = len(self) - (len(self) // 100)
                for _ in range(cull):
                    self.pop()

        for (i, c1) in enumerate(words):
            for (j, c2) in enumerate(words[i+1:], i + 1):
                dot[(i, j)] = c1 - c2
                
        return np.transpose(np.fliplr(np.triu(dot)))
        
    def dotplot(self, sim, fname):
        extent = [ 0, len(sim) ] * 2
        plt.imshow(sim, interpolation='none', extent=extent)
        
        plt.grid('off')
        plt.tight_layout()
        
        plt.savefig(fname)
