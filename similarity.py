import math
import logger

import numpy as np
import operator as op
import multiprocessing as mp
import matplotlib.pyplot as plt

from itertools import combinations

def quadratic(a, b, c):
    numerator = math.sqrt(b ** 2 - 4 * a * c)
    denominator = 2 * a

    return [ f(-b, numerator) / denominator for f in (op.add, op.sub) ]

class SimilarityMatrix(dict):
    def __init__(self, fragments, distance=op.eq, parallel=None):
        if parallel is not None:
            parallel = min(mp.cpu_count(), max(parallel, 1))

        with mp.Pool(parallel) as pool:
            p = pool.imap_unordered
            for i in p(self.f, self.enum(distance, fragments)):
                self.update(i)
    
    def enum(self, distance, fragments):
        raise NotImplementedError

    def f(self, args):
        raise NotImplementedError

    def to_numpy(self, orient=True, mirror=False, dtype=np.float16):
        length = max(quadratic(1/2, 1/2, -len(self)))
        assert(length.is_integer())
    
        dots = np.zeros([ int(length) + 1 ] * 2, dtype=dtype)
        for (key, value) in self.items():
            dots[key] = value
        np.fill_diagonal(dots, 1)
        
        if orient:
            dots = np.transpose(np.fliplr(dots))
            
        return dots
        
    def dotplot(self, fname, dots=None):
        if dots is None:
            dots = self.to_numpy()
            
        extent = [ 0, len(dots) ] * 2
        plt.imshow(dots, interpolation='none', extent=extent)
        
        plt.grid('off')
        plt.tight_layout()
        
        plt.savefig(fname)

class ComparisonPerCPU(SimilarityMatrix):
    def enum(self, distance, fragments):
        for i in combinations(range(len(fragments)), 2):
            strings = [ fragments.at(x) for x in i ]
            yield (i, strings, distance)
        
    def f(self, args):
        (index, strings, distance) = args
        return { index: distance(*strings) }

class RowPerCPU(SimilarityMatrix):
    def enum(self, distance, fragments):
        log = logger.getlogger(True)
        
        for i in range(len(fragments)):
            log.info(i)
            yield (i, fragments, distance)

    def f(self, args):
        (index, fragments, distance) = args
       
        s1 = fragments.at(index)
        j = index + 1
        iterable = enumerate(fragments.strings(j), j)

        logger.getlogger().info(j)
        
        return { (index, i): distance(s1, s2) for (i, s2) in iterable }
