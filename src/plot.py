import numpy as np
from pathlib import Path
from argparse import ArgumentParser

import zrtlib.dotplot as dp

arguments = ArgumentParser()
arguments.add_argument('--mmap')
arguments.add_argument('--shape', type=int)
args = arguments.parse_args()

# 20625
shape = ( args.shape, ) * 2
dots = np.memmap(args.mmap, dtype=np.float16, mode='r', shape=shape)

output = Path(args.mmap).with_suffix('.png')
dp.plot(dots, str(output))
