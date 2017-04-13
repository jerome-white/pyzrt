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
from zrtlib import zutils
from zrtlib.indri import QueryDoc

def func(args):
    (path, metric) = args

    log = logger.getlogger()
    log.info(path)

    with path.open() as fp:
        results = { x: y[metric] for (x, y) in zutils.read_trec(fp) }

    return (pd.DataFrame.from_dict(results, orient='index').
            reset_index().
            assign(topic=int(QueryDoc.components(path).topic)).
            rename(columns={ 'index': 'query', 0: 'metric' }).
            apply(pd.to_numeric).
            sort_values(by=[ 'topic', 'query' ]))

def aquire(args):
    with Pool() as pool:
        iterable = map(lambda x: (x, args.metric), args.top_level.iterdir())
        yield from pool.imap_unordered(func, iterable)

arguments = ArgumentParser()
arguments.add_argument('--metric')
arguments.add_argument('--top-level', type=Path)
args = arguments.parse_args()

df = pd.concat(aquire(args))
# df.to_pickle('progressive.pkl')

sns.set_context('poster')
sns.set(font_scale=1.7)
ax = sns.tsplot(time='query',
                value='metric',
                condition='topic',
                data=df,
                ci=30)
# ax.set(xlim=(None, df['guess'].max()),
#        ylim=(0, None))
ax.figure.savefig('progressive.png', bbox_inches='tight')
