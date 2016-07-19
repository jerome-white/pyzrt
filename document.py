import logger
import segment

import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

class Document:
    def __init__(self, fname, docno, data):
        self.fname = fname
        self.docno = docno
        self.data = data

class Corpus(list):
    def __str__(self):
        return ' '.join([ x.data for x in self ])

    def similarity(self):
        while True:
            words = segment.Sampler(str(self), 1000, segment.Sequence)
            try:
                shape = [ len(words) ] * 2
                dot = np.ones(shape, dtype=np.float16)
                break
            except MemoryError:
                cull = len(self) - (len(self) // 100)
                for _ in range(cull):
                    self.pop()

        for (i, c1) in enumerate(words):
            following = i + 1
            for (j, c2) in enumerate(words[following:], following):
                dot[(i, j)] = c1 - c2
                
        return np.transpose(np.fliplr(np.triu(dot)))
        
    def dotplot(self, sim, fname):
        extent = [ 0, len(sim) ] * 2
        plt.imshow(sim, interpolation='none', extent=extent)
        
        plt.grid('off')
        plt.tight_layout()
        
        plt.savefig(fname)
