import csv
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

from zrtlib import logger
from zrtilib import zutils
from zrtlib.indri import QueryDoc

def aquire(path, metric, baseline=None):
    index_col = 'guess'
    df = pd.read_csv(str(path),
                     index_col=index_col,
                     usecols=[ index_col, metric ],
                     squeeze=True)
    df.name = QueryDoc.components(path).topic
    df = df.reindex(index=np.arange(1, df.index.max() + 1)).ffill().fillna(0)

    if baseline is not None:
        df /= baseline[df.name]

    return df

def func(args):
    (path, opts) = args

    title = path.stem
    output = opts.output.joinpath(title).with_suffix('.png')

    if opts.baseline is not None:
        baseline = dict(zutils.read_baseline(opts.baseline, opts.metric))
    else:
        baseline = None

    frames = [ aquire(x, opts.metric, baseline) for x in path.iterdir() ]
    if not frames:
        return
    df = pd.concat(frames, axis='columns')

    ymax = 1 if df.max().max() < 1 else None
    ylabel = opts.metric
    if baseline:
        ylabel = 'Fraction of baseline ' + ylabel

    matplotlib.style.use('ggplot')
    plt.clf()
    df.plot(title=title.title(),
            grid=True,
            legend=False,
            ylim=(0, ymax))
    plt.xlabel('Guess')
    plt.ylabel(ylabel)
    plt.savefig(str(output), bbox_inches='tight')

    return path.stem

arguments = ArgumentParser()
arguments.add_argument('--metric')
arguments.add_argument('--top-level', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--baseline', type=Path)
args = arguments.parse_args()

log = logger.getlogger(True)

with Pool() as pool:
    iterable = map(lambda x: (x, args), args.top_level.iterdir())
    for i in filter(None, pool.imap_unordered(func, iterable)):
        log.info(i)
