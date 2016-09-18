import operator as op
from pathlib import Path
from collections import namedtuple, defaultdict

import numpy as np

import logger

IndexedToken = namedtuple('IndexedToken', 'index, tokens')

class Posting(defaultdict):
    def __init__(self, token_stream, to_string):
        super().__init__(list)

        for (i, tokens) in enumerate(token_stream):
            tok = to_string(tokens)
            self[tok].append(IndexedToken(i, tokens))
    
    def frequency(self, token):
        return len(self[token])

    def mass(self, token, relative=True):
        counter = { x: sum([ len(z) for z in y ]) for (x, y) in self.items() }
        c = counter[token]

        return c / sum(counter.values()) if relative else c

    def weight(self, token):
        freq = self.frequency(token)
        keys = set(self.keys())
        
        n = max(map(self.frequency, keys.difference([ token ])))

        return freq / n

    def each(self, index):
        yield from map(op.attrgetter('index'), self[index])

    def tokens(self):
        sum([ len(x) * len(y) for (x, y) in self.items() ])

class Dotplot:
    def __init__(self, total_elements, compression_ratio=1):
        assert(0 < compression_ratio <= 1)
        
        self.N = total_elements
        self.n = round(self.N * compression_ratio)
        self.dots = self.mkdots(( self.n, ) * 2)

    def mkdots(self, shape):
        return np.zeros(shape)

    def cell(self, x):
        return (x * self.n) // self.N
    
    def update(self, row, col, value):
        coordinates = tuple(map(self.cell, [ row, col ]))
        self.dots[coordinates] += value

class DistributedDotplot(Dotplot):
    def __init__(self, total_elements, compression_ratio=1, map_file=None):
        self.mmap = map_file
        super().__init__(total_elements, compression_ratio)

    def mkdots(self, shape):
        log = logger.getlogger(True)
        log.debug('{0} {1}'.format(self.mmap, shape))
        return np.memmap(self.mmap, dtype=np.float16, mode='w+', shape=shape)
