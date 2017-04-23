from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

from zrtlib import logger
from zrtlib.indri import QueryDoc

def aquire(path, metric):
    index_col = 'guess'
    df = pd.read_csv(str(path),
                     index_col=index_col,
                     usecols=[ index_col, metric ],
                     squeeze=True)
    df.name = QueryDoc.components(path).topic

    return df.reindex(index=np.arange(1, df.index.max() + 1)).ffill()

def func(args):
    (path, opts) = args

    title = path.stem
    output = opts.output.joinpath(title).with_suffix('.png')

    frames = [ aquire(x, opts.metric) for x in path.iterdir() ]
    if not frames:
        return

    df = pd.concat(frames, axis='columns')

    matplotlib.style.use('ggplot')
    plt.clf()
    df.plot(title=title.title(),
            grid=True,
            legend=False,
            ylim=(0, 1))
    plt.xlabel('Guess')
    plt.ylabel(opts.metric)
    plt.savefig(str(output), bbox_inches='tight')

    return path.stem

arguments = ArgumentParser()
arguments.add_argument('--metric')
arguments.add_argument('--top-level', type=Path)
arguments.add_argument('--output', type=Path)
args = arguments.parse_args()

log = logger.getlogger(True)

with Pool() as pool:
    iterable = map(lambda x: (x, args), args.top_level.iterdir())
    for i in filter(None, pool.imap_unordered(func, iterable)):
        log.info(i)
