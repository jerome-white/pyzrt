import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from collections import Counter

import pandas as pd
import matplotlib.pyplot as plt

import pyzrt as pz

def func(args):
    log = pz.util.get_logger()

    return pd.read_csv(args, index_col=0, squeeze=True)
    
arguments = ArgumentParser()
arguments.add_argument('--terms', type=Path)
arguments.add_argument('--plot', type=Path)
arguments.add_argument('--save', type=Path)
arguments.add_argument('--creator')
arguments.add_argument('--x-min', type=float, default=0)
arguments.add_argument('--normalize', action='store_true')
args = arguments.parse_args()

with mp.Pool(args.workers, func, (outgoing, incoming, args.creator)):
    df = pd.DataFrame()
    for i in args.terms.iterdir():
        pass

log = pz.util.get_logger(True)

img = args.plot.joinpath(i).with_suffix('.png')
if args.normalize:
    df /= df.sum()

df.plot.line(grid=True, xlim=(args.x_min, None))

plt.savefig(str(img), bbox_inches='tight')

log.info('END')
