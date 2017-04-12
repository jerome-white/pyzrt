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

    return df.reindex(index, method='ffill').reset_index().assign(**columns)

def max_guesses(path):
    with path.open() as fp:
        reader = csv.DictReader(fp)
        guesses = [ int(x['guess']) for x in reader ]

    return (path, max(guesses))

def byline(args):
    guess_count = collections.defaultdict(list)
    largest = collections.defaultdict(int)

    with Pool() as pool:
        iterable = args.top_level.glob(Path('**', QueryDoc.prefix + '*'))
        for (path, guesses) in pool.imap_unordered(max_guesses, iterable):
            strategy = path.parts[-2]
            guess_count[strategy].append((path, guesses))
            largest[strategy] = max(largest[strategy], guesses)

    for (strategy, data) in guess_count.items():
        n = largest[strategy]
        for (path, guesses) in data:
            ratio = 1 - (n - guesses) / n
            if ratio >= args.threshold:
                yield (path, args)

def byoption(args):
    (path, options) = args

    if options.include and str(path) not in options.include:
        return

    if options.strategy:
        strategy = path.parts[-2]
        if strategy not in options.strategy:
            return

    if options.topics:
        qid = QueryDoc.components(path)
        if qid.topic not in options.topics:
            return

    yield (path, options.metric)

def aquire(args):
    with Pool() as pool:
        iterable = filter(None, byoption(byline(args)))
        print(list(iterable))
        exit()
        yield from pool.imap_unordered(func, iterable)

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
