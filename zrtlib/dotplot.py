import random
import numpy as np
import matplotlib.pyplot as plt
from uuid import uuid4

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
    def __init__(self, total_elements, compression_ratio=1, map_file=None):
        self.mmap = map_file
        super().__init__(total_elements, compression_ratio)

    def mkdots(self, shape):
        (*parts, name) = self.mmap.parts

        while True:
            (c, _) = str(uuid4()).split('-', 1)
            fname = name + '-' + c
            path = Path(*parts, fname).with_suffix(str(self.n))
            if not path.exists():
                break
            log.debug('{0} exists!'.format(path))

        return np.memmap(str(path), dtype=np.float16, mode='w+', shape=shape)

def plot(dots, output):
    extent = [ 0, len(dots) ] * 2
    plt.imshow(dots, cmap='Greys', interpolation='none', extent=extent)
        
    plt.grid('off')
    plt.tight_layout()
        
    plt.savefig(output)
