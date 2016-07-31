import logger
import segment

import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import multiprocessing as mp

from collections import namedtuple

Document = namedtuple('Document', 'fpath, data')

def fragment(corpus, segments):
    blocks = []
    
    for fragment in segments:
        string = []
        for (docno, start, stop) in fragment:
            s = corpus[docno].data[start:end]
            string.append(s)
        blocks.append(mkstring(''.join(string)))

    return blocks
        
def enum(blocks, offset):
    idx = offset + 1
    s1 = blocks[offset]

    for (i, s2) in enumerate(blocks[idx:], idx):
        yield (i, s1, s2)
        
def distance(args):
    (col, s1, s2) = args
    return (col, s1 - s2)

def similarity(blocks, mkstring, parallel=1):
    matrix = {}
    
    with mp.Pool(parallel) as pool:
        f = pool.imap_unordered
        for i in range(len(blocks)):
            for (j, value) in f(distance, enum(blocks, i)):
                matrix[(i, j)] = value

    return matrix

def to_numpy(matrix, orient=True, mirror=False, dtype=np.float16):
    dot = np.zeros([ len(matrix) ] * 2, dtype=dtype)
    dot[matrix.keys()] = matrix.values()
    np.fill_diagonal(dot, 1)
        
    if orient:
        dot = np.transpose(np.fliplr(dot))
            
    return dot
        
def dotplot(from_numpy, fname):
    extent = [ 0, len(from_numpy) ] * 2
    plt.imshow(from_numpy, interpolation='none', extent=extent)
    
    plt.grid('off')
    plt.tight_layout()
    
    plt.savefig(fname)
