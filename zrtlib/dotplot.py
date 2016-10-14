import numpy as np

# from zrtlib import logger

class Dotplot:
    def __init__(self, total_elements, map_file, compression_ratio=1,
                 init_map=False):
        assert(0 < compression_ratio <= 1)
        
        self.N = total_elements
        self.n = round(self.N * compression_ratio)

        kwargs = {
            'filename': str(map_file),
            'shape': ( self.n, ) * 2,
            'mode': 'w+' if init_map else 'r+',
            'dtype': np.float16,
        }
        self.matrix = np.memmap(**kwargs)

    def cell(self, x):
        return (x * self.n) // self.N
    
    def update(self, row, col, value):
        coordinates = tuple(map(self.cell, [ row, col ]))
        self.matrix[coordinates] += value
