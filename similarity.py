import math
# import logger
import operator as op

import numpy as np
import matplotlib.pyplot as plt
import multiprocessing as mp

###########################################################################

def enum(blocks, offset):
    idx = offset + 1
    s1 = blocks[offset]

    for (i, s2) in enumerate(blocks[idx:], idx):
        yield (i, s1, s2)
        
def distance(args):
    (col, s1, s2) = args
    return (col, s1 - s2)

def quadratic(a, b, c):
    numerator = math.sqrt(b ** 2 - 4 * a * c)
    denominator = 2 * a

    return [ f(-b, numerator) / denominator for f in (op.add, op.sub) ]

###########################################################################

def chunk(corpus, segments, mkstring):
    blocks = []
    
    for fragment in segments:
        string = []
        for (docno, start, end) in fragment:
            s = corpus[docno].data[start:end]
            string.append(s)
        blocks.append(mkstring(''.join(string)))

    return blocks

def similarity(blocks, parallel=None):
    if parallel is not None:
        parallel = min(mp.cpu_count(), max(parallel, 1))
        
    matrix = {}
    
    with mp.Pool(parallel) as pool:
        f = pool.imap_unordered
        for (i, _) in enumerate(blocks):
            for (j, value) in f(distance, enum(blocks, i)):
                matrix[(i, j)] = value

    return matrix

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
