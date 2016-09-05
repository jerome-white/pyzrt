import operator as op
from collections import namedtuple, defaultdict

import numpy as np

import similarity
from corpus import to_string

IndexedFragment = namedtuple('IndexedFragment',
                             [ 'index' ] + list(similarity.Fragment._fields))

class Posting(defaultdict):
    def __init__(self, fragments, corpus=None):
        super().__init__(list)

        index = 0
        for (_, i) in map(list, similarity.frag(fragments)):
            token = to_string(i, corpus)
            for (j, k) in enumerate(i, index):
                self[token].append(IndexedFragment(j, *k))
            index = j + 1
    
    def frequency(self, token):
        return len(self[token]) if token in self else 0

    def weight(self, token):
        freq = self.frequency(token)
        keys = set(self.keys())
        
        n = max(map(self.frequency, keys.difference([ token ])))

        return freq / n

    def each(self, index):
        yield from map(op.itemgetter(0), self[index])

class Dotplot:
    def __init__(self, total_elements, map_file=None, compression_ratio=1):
        assert(0 < compression_ratio <= 1)
        
        self.N = total_elements
        self.n = round(self.N * compression_ratio)
        shape = [ self.n ] * 2
        
        if map_file:
            self.dots = np.memmap(map_file, dtype=np.float16, shape=shape)
        else:
            self.dots = np.zeros(shape)

    def cell(self, x):
        return (x * self.n) / self.N
    
    def update(self, row, col, value):
        coordinates = tuple(map(self.cell, [ row, col ]))
        self.dots[coordinates] += value
