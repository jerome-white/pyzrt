import numpy as np

from collections import namedtuple

Document = namedtuple('Document', 'fpath, data')
Fragment = namedtuple('Segment', 'docno, start, end')

def orange(start, stop, step, offset=None):
    i = start
    while i < stop:
        if offset is not None:
            j = i + offset
            offset = None
        else:
            j = i + step
        j = min(j, stop)
            
        yield (i, j)
        i = j

def segment(corpus, block_size=1):
    remaining = None
    fragments = []
    length = 0
    
    for (docno, document) in corpus.items():
        for (i, j) in orange(0, len(document.data), block_size, remaining):
            f = Fragment(docno, i, j)
            fragments.append(f)
            length += j - i
                
            if length == block_size:
                yield fragments
                
                remaining = None
                fragments = []
                length = 0

        if fragments:
            remaining = block_size - length

    if fragments:
        yield fragments
