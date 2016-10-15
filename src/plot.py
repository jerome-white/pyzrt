import math
import numpy as np
from pathlib import Path
from argparse import ArgumentParser

import matplotlib.pyplot as plt
from skimage.transform import rescale

# import zrtlib.dotplot as dp

arguments = ArgumentParser()
arguments.add_argument('--mmap', type=Path)
arguments.add_argument('--scale', type=float)
args = arguments.parse_args()

dots = np.memmap(str(args.mmap), dtype=np.float16, mode='r')
dots = dots / max(dots)

dim = math.sqrt(dots.size)
assert(dim.is_integer())

shape = (int(dim),) * 2
dots = dots.reshape(shape)
if args.scale:
    dots = rescale(dots, args.scale)

output = args.mmap.with_suffix('.png')
# dp.plot(dots, str(output))

# extent = [ 0, len(dots) ] * 2
# plt.imshow(dots, cmap='Greys', interpolation='none', extent=extent)
plt.imshow(dots, cmap='Greys', interpolation='none')

plt.grid('off')
plt.tight_layout()

plt.savefig(output)
