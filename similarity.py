import math
import logger
import itertools

import numpy as np
import operator as op
import multiprocessing as mp
import matplotlib.pyplot as plt

###########################################################################

def enum(distance, blocks):
    # http://stackoverflow.com/a/27151051
    for i in itertools.combinations(enumerate(blocks), 2):
        yield (distance, *[ x for x in zip(*i) ])
        
def f(args):
    (distance, index, strings) = args
    return (index, distance(*strings))

def quadratic(a, b, c):
    numerator = math.sqrt(b ** 2 - 4 * a * c)
    denominator = 2 * a

    return [ f(-b, numerator) / denominator for f in (op.add, op.sub) ]

###########################################################################

def similarity(blocks, distance=op.eq, parallel=None):
    if parallel is not None:
        parallel = min(mp.cpu_count(), max(parallel, 1))

    with mp.Pool(parallel) as pool:
        p = pool.imap_unordered
        return { i: j for (i, j) in p(f, enum(distance, blocks)) }

def to_numpy(matrix, orient=True, mirror=False, dtype=np.float16):
    length = max(quadratic(1/2, 1/2, -len(matrix)))
    assert(length.is_integer())
    
    dots = np.zeros([ int(length) + 1 ] * 2, dtype=dtype)
    for (key, value) in matrix.items():
        dots[key] = value
    np.fill_diagonal(dots, 1)
        
    if orient:
        dots = np.transpose(np.fliplr(dots))
            
    return dots
        
def dotplot(dots, fname):
    extent = [ 0, len(dots) ] * 2
    plt.imshow(dots, interpolation='none', extent=extent)
    
    plt.grid('off')
    plt.tight_layout()
    
    plt.savefig(fname)
