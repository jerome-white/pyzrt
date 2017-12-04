from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

import pandas as pd
import matplotlib.pyplot as plt

import pyzrt as pz

def func(args):
    (stats, measurement) = args

    df = pd.read_csv(stats)
    if measurement in df.columns:
        return df

def aquire(measurement, directory):
    with Pool() as pool:
        iterable = map(lambda x: (x, measurement), directory.iterdir())
        yield from pool.imap_unordered(func, iterable)

arguments = ArgumentParser()
arguments.add_argument('--terms', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--measurement')
arguments.add_argument('--x-min', type=float, default=0)
arguments.add_argument('--normalize', action='store_true')
args = arguments.parse_args()

df = pd.concat(aquire(args.measurement, args.terms))
assert(not df.empty)

df = df.pivot(index='count', columns='version', values=args.measurement)
if args.normalize:
    df /= df.sum()
df.plot.line(grid=True, xlim=(args.x_min, None))

img = args.output.joinpath(args.measurement).with_suffix('.png')
plt.savefig(str(img), bbox_inches='tight')