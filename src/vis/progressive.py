import csv
import operator as op
import collections
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

from zrtlib import logger
from zrtlib import zutils
from zrtlib.indri import QueryDoc

def func(args):
    (path, opts) = args

    with path.open() as fp:
        df = pd.Series({x: y[opts.metric] for (x, y) in zutils.read_trec(fp)})
        if opts.has_relevant and df.max() == 0:
            return (path.stem, False)

    topic = QueryDoc.components(path).topic
    output = opts.output.joinpath(topic).with_suffix('.png')

    matplotlib.style.use('ggplot')
    plt.clf()
    df.plot(title=topic,
            grid=True,
            legend=False,
            ylim=(0, 1))
    plt.xlabel('Terms revealed')
    plt.ylabel(opts.metric)
    plt.savefig(str(output), bbox_inches='tight')

    return (path.stem, True)

arguments = ArgumentParser()
arguments.add_argument('--metric')
arguments.add_argument('--output', type=Path)
arguments.add_argument('--top-level', type=Path)
arguments.add_argument('--has-relevant', action='store_true')
args = arguments.parse_args()

log = logger.getlogger(True)

with Pool() as pool:
    iterable = map(lambda x: (x, args), args.top_level.iterdir())
    for (i, j) in pool.imap_unordered(func, iterable):
        log.error(i) if not j else log.info(i)
