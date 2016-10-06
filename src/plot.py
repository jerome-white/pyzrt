import math
import numpy as np
from pathlib import Path
from argparse import ArgumentParser

import zrtlib.dotplot as dp

arguments = ArgumentParser()
arguments.add_argument('--mmap', type=Path)
args = arguments.parse_args()

dots = np.memmap(str(args.mmap), dtype=np.float16, mode='r')
dim = math.sqrt(dots.size)
assert(dim.is_integer())

shape = (int(dim),) * 2
dots = dots.reshape(shape)

output = args.mmap.joinpath().with_suffix('.png')
dp.plot(dots, str(output))
