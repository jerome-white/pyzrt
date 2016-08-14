import math

import numpy as np
import operator as op
import matplotlib.pyplot as plt

from scipy import constants

def quadratic(a, b, c):
    numerator = math.sqrt(b ** 2 - 4 * a * c)
    denominator = 2 * a

    return [ f(-b, numerator) / denominator for f in (op.add, op.sub) ]

def to_numpy(self, similarity, orient=True, mirror=False, dtype=np.float16):
    length = max(quadratic(1/2, 1/2, -len(similarity)))
    assert(length.is_integer())
    
    dots = np.zeros([ int(length) + 1 ] * 2, dtype=dtype)
    for (key, value) in similarity:
        dots[key] = value
    np.fill_diagonal(dots, 1)
        
    if orient:
        dots = np.transpose(np.fliplr(dots))
            
    return dots
        
def dotplot(self, dots, output):
    extent = [ 0, len(dots) ] * 2
    plt.imshow(dots, interpolation='none', extent=extent)
        
    plt.grid('off')
    plt.tight_layout()
        
    plt.savefig(output)
