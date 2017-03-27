import csv
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

import numpy as np
import pandas as pd
import seaborn as sns

from zrtlib.indri import QueryDoc

def func(args):
    (path, metric) = args

    index = 'guess'
    df = pd.read_csv(str(path),
                     index_col=index,
                     usecols=[ index, metric ])

    index = np.arange(df.index.min(), df.index.max())
    columns = dict(zip(('strategy', 'topic'), path.parts[-2:]))

    return df.reindex(index, method='ffill').reset_index().assign(**columns)

def each(args):
    topics = set(args.topic)

    for i in args.top_level.glob('**/' + QueryDoc.prefix + '*'):
        qid = QueryDoc.components(i)
        if not topics or qid.topic in topics:
            yield (i, args.metric)

def aquire(args):
    with Pool() as pool:
        yield from pool.imap_unordered(func, each(args))

arguments = ArgumentParser()
arguments.add_argument('--metric')
arguments.add_argument('--top-level', type=Path)
arguments.add_argument('--topic', action='append', default=[])
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
ax.figure.savefig('flips.png', bbox_inches='tight')
