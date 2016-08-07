import math
import logger
import itertools

import numpy as np
import operator as op
import multiprocessing as mp
import matplotlib.pyplot as plt

def quadratic(a, b, c):
    numerator = math.sqrt(b ** 2 - 4 * a * c)
    denominator = 2 * a

    return [ f(-b, numerator) / denominator for f in (op.add, op.sub) ]

class SimilarityMatrix:
    def enum(self, distance, blocks):
        raise NotImplementedError

    def f(self, args):
        raise NotImplementedError

    def similarity(self, blocks, distance=op.eq, parallel=None):
        if parallel is not None:
            parallel = min(mp.cpu_count(), max(parallel, 1))

        d = {}
        with mp.Pool(parallel) as pool:
            for i in pool.imap_unordered(self.f, self.enum(distance, blocks)):
                d.update(i)

        return d

    def to_numpy(self, matrix, orient=True, mirror=False, dtype=np.float16):
        length = max(quadratic(1/2, 1/2, -len(matrix)))
        assert(length.is_integer())
    
        dots = np.zeros([ int(length) + 1 ] * 2, dtype=dtype)
        for (key, value) in matrix.items():
            dots[key] = value
        np.fill_diagonal(dots, 1)
        
        if orient:
            dots = np.transpose(np.fliplr(dots))
            
        return dots
        
    def dotplot(self, dots, fname):
        extent = [ 0, len(dots) ] * 2
        plt.imshow(dots, interpolation='none', extent=extent)
        
        plt.grid('off')
        plt.tight_layout()
        
        plt.savefig(fname)

class ComparisonPerCPU(SimilarityMatrix):
    def enum(self, distance, blocks):
        # http://stackoverflow.com/a/27151051
        for i in itertools.combinations(enumerate(blocks), 2):
            yield (*[ x for x in zip(*i) ], distance)
        
    def f(self, args):
        (index, strings, distance) = args
        return { index: distance(*strings) }

class RowPerCPU(SimilarityMatrix):
    def enum(self, distance, blocks):
        blks = list(blocks)
        for i in range(len(blks)):
            yield (i, blks, distance)

    def f(self, args):
        (index, blocks, distance) = args

        d = {}
        s1 = blocks[index]
        for (i, s2) in enumerate(blocks):
            if i > index:
                d[(index, i)] = distance(s1, s2)

        return d
