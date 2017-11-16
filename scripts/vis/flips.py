import csv
import operator as op
import collections
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

import numpy as np
import pandas as pd
import seaborn as sns

from zrtlib import logger
from zrtlib.indri import QueryDoc

def func(args):
    (path, metric) = args

    log = logger.getlogger()
    log.info(path)

    index_col = 'guess'
    df = pd.read_csv(str(path),
                     index_col=index_col,
                     usecols=[ index_col, metric ])

    index = np.arange(df.index.min(), df.index.max() + 1)
    columns = dict(zip(('strategy', 'topic'), path.parts[-2:]))

    return df.reindex(index).reset_index().ffill().assign(**columns)

def max_guesses(path):
    with path.open() as fp:
        reader = csv.DictReader(fp)
        guesses = [ int(x['guess']) for x in reader ]

    return (path, max(guesses))

def byoption(args, path):
    if args.include and str(path) not in args.include:
        return

    if args.strategy:
        strategy = path.parts[-2]
        if strategy not in args.strategy:
            return

    if args.topic:
        qid = QueryDoc.components(path)
        if qid.topic not in args.topic:
            return

    yield path

def byline(args):
    guess_count = collections.defaultdict(list)
    largest = collections.defaultdict(int)

    log = logger.getlogger()

    with Pool() as pool:
        iterable = args.top_level.glob(str(Path('**', QueryDoc.prefix + '*')))
        for (pth, guesses) in pool.imap_unordered(max_guesses, iterable):
            strategy = pth.parts[-2]
            guess_count[strategy].append((pth, guesses))
            largest[strategy] = max(largest[strategy], guesses)

    for (strategy, data) in guess_count.items():
        n = largest[strategy]
        for (pth, guesses) in data:
            log.info('{0} {1}'.format(pth, guesses))

            ratio = 1 - (n - guesses) / n
            if ratio >= args.threshold:
                yield pth

def each(args):
    for i in byline(args):
        for j in byoption(args, i):
            yield (j, args.metric)

def aquire(args):
    with Pool() as pool:
        yield from pool.imap_unordered(func, each(args))

arguments = ArgumentParser()
arguments.add_argument('--metric')
arguments.add_argument('--top-level', type=Path)
arguments.add_argument('--threshold', type=float, default=1.0)
arguments.add_argument('--topic', action='append', default=[])
arguments.add_argument('--include', action='append', default=[])
arguments.add_argument('--strategy', action='append', default=[])
args = arguments.parse_args()

df = pd.concat(aquire(args))

sns.set_context('paper')
sns.set(font_scale=1.7)
ax = sns.tsplot(time='guess',
                value=args.metric,
                unit='topic',
                condition='strategy',
                data=df,
                ci=30)
ax.set(xlim=(None, df['guess'].max()),
       ylim=(0, None))
ax.figure.savefig('flips.png', bbox_inches='tight')
