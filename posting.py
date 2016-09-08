import operator as op
from collections import namedtuple, defaultdict

import numpy as np

import logger
from corpus import to_string
from similarity import Fragment, frag

IndexedFragment = namedtuple('IndexedFragment',
                             [ 'index' ] + list(Fragment._fields))

class Posting(defaultdict):
    def __init__(self, fragments, corpus=None):
        super().__init__(list)

        index = 0
        for (_, i) in map(list, frag(fragments)):
            token = to_string(i, corpus)
            for (j, k) in enumerate(i, index):
                self[token].append(IndexedFragment(j, *k))
            index = j + 1
    
    def frequency(self, token):
        return len(self[token]) if token in self else 0

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
        yield from map(op.itemgetter(0), self[index])

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
