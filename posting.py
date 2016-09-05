import operator as op
from collections import namedtuple, defaultdict

import corpus
import similarity

IndexedFragment = namedtuple('IndexedFragment',
                             [ 'index' ] + list(similarity.Fragment._fields))

class Posting(defaultdict):
    def __init__(self, fragments, corpus=None):
        super().__init__(list)

        for (i, frg) in enumerate(similarity.frag(fragments)):
            token = to_string(frg, corpus)
            value = IndexedFragment(i, *frg)
            self[token].append(value)
    
    def frequency(self, token):
        return len(self[token]) if token in self else 0

    def weight(self, token):
        freq = self.frequency(token)
        keys = set(self.keys())
        
        n = max(map(self.frequency, keys.difference([ token ])))

        return freq / n

    def each(self, index):
        yield from map(op.itemgetter(-1), self[index])

class Dotplot:
    def __init__(self, total_elements, map_file=None, compression_ratio=1):
        assert(0 < compression_ratio <= 1)
        
        self.N = total_elements
        self.n = round(self.N * compression_ratio)
        shape = [ self.n ] * 2
        
        if map_file:
            self.dots = np.memmap(map_file, dtype=np.float16, mode='w+',
                                  shape=shape)
        else:
            self.dots = np.zeros(shape)

    def cell(self, x):
        return (x * self.n) / self.N
    
    def update(self, row, col, value):
        coordinates = tuple(map(self.cell, [ row, col ]))
        self.dots[coordinates] += value
