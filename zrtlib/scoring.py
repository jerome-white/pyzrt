import math
from collections import Counter

import numpy as np

class OkapiBM25:
    def __init__(self, index, k=1.2, b=0.75):
        self.k = k
        self.b = b
        
        self.dlengths = Counter()
        for (_, tokens) in index.each():
            for i in tokens:
                for j in i.documents():
                    self.dlengths[j] += 1

        self.N = len(self.dlengths.keys())
        self.avgdl = np.mean(self.dlengths.values())
        assert(self.avgdl > 0)

    def score(self, document, query):
        rsv = 0
        norm = 1 - self.b + self.b * self.dlengths[document] / self.avgdl
        
        for q in query:
            n = 0
            freq = 0
            for i in self.index.get(q):
                n += 1
                if i.docno == document:
                    freq += 1

            if freq > 0:
                idf = math.log((self.N - n + 0.5) / (n + 0.5))
                tf = freq * (self.k + 1) / (freq + self.k * norm)

                rsv += idf * tf

        return rsv
