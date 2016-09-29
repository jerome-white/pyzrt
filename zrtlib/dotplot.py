import random
import numpy as np
import matplotlib.pyplot as plt
from uuid import uuid4
from pathlib import Path

from zrtlib import logger

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
    def __init__(self, total_elements, compression_ratio=1, map_file=None,
                 init_map=False):
        self.mmap = map_file
        self.mode = 'write' if init_map else 'readwrite'

        super().__init__(total_elements, compression_ratio)

    def mkdots(self, shape):
        suffix = '.' + str(self.n)
        fname = str(self.mmap.with_suffix(suffix))

        return np.memmap(fname, mode=self.mode, dtype=np.float16, shape=shape)

def plot(dots, output):
    extent = [ 0, len(dots) ] * 2
    plt.imshow(dots, cmap='Greys', interpolation='none', extent=extent)
        
    plt.grid('off')
    plt.tight_layout()
        
    plt.savefig(output)
