import logger
import segment

import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import multiprocessing as mp

class Document:
    def __init__(self, fname, docno, data):
        self.fname = fname
        self.docno = docno
        self.data = data

def enum(words, offset):
    idx = offset + 1
    s1 = words[offset]

    for (i, s2) in enumerate(words[idx:], idx):
        yield (i, s1, s2)
        
def distance(args):
    (col, s1, s2) = args
    return (col, s1 - s2)
        
class Corpus(list):
    def __str__(self):
        return ' '.join([ x.data for x in self ])

    def similarity(self, segmenter, parallel=1, orient=True):
        if parallel is not None:
            parallel = min(mp.cpu_count(), max(parallel, 1))
        
        while True:
            words = list(segmenter.segment(str(self)))
            try:
                shape = [ len(words) ] * 2
                dot = np.zeros(shape, dtype=np.float16)
                break
            except MemoryError:
                cull = len(self) - (len(self) // 100)
                for _ in range(cull):
                    self.pop()

        with mp.Pool(parallel) as pool:
            f = pool.imap_unordered
            for i in range(len(words)):
                for (j, value) in f(distance, enum(words, i)):
                    dot[(i, j)] = value
        np.fill_diagonal(dot, 1)

        if orient:
            return np.transpose(np.fliplr(dot))
        else:
            return dot
        
    def dotplot(self, sim, fname):
        extent = [ 0, len(sim) ] * 2
        plt.imshow(sim, interpolation='none', extent=extent)
        
        plt.grid('off')
        plt.tight_layout()
        
        plt.savefig(fname)
