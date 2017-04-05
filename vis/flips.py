import csv
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

    index = np.arange(df.index.min(), df.index.max())
    columns = dict(zip(('strategy', 'topic'), path.parts[-2:]))

    return df.reindex(index, method='ffill').reset_index().assign(**columns)

def each(args):
    topics = set(args.topic)
    path = Path('**', QueryDoc.prefix + '*')

    for i in args.top_level.glob(str(path)):
        if args.strategy:
            strategy = i.parts[-2]
            if strategy not in args.strategy:
                continue

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
print(df.iloc[df['guess'].argmax()])
ax.set(xlim=(None, df['guess'].max()),
       ylim=(0, None))
ax.figure.savefig('flips.png', bbox_inches='tight')
