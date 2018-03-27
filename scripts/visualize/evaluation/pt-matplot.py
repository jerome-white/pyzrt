import sys
import operator as op
from pathlib import Path
from argparse import ArgumentParser

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

arguments = ArgumentParser()
arguments.add_argument('--output', type=Path)
arguments.add_argument('--valid-queries', type=Path)
arguments.add_argument('--min-relevant', type=int, default=0)
args = arguments.parse_args()

# metric_label = {
#     'map': 'MAP',
#     'recip_rank': 'Mean Reciprocal Rank',
#     'ndcg': 'NDCG',
# }

df = pd.read_csv(sys.stdin)
df = df[df['num_rel'] >= args.min_relevant]
if args.valid_queries:
    with args.valid_queries.open() as fp:
        good = [ 'Q' + x.strip().zfill(3) for x in fp ]
    df = df[df['query'].isin(good)]

if df.columns.contains('value_baseline'):
    normalization = op.sub
    original = 'value_original'
    df = df.rename(columns={'value': original})
    df = df.assign(value=normalization(df[original], df['value_baseline']))
df.to_csv('b', index=False)

# plt.style.use('ggplot')
(figure, axes) = plt.subplots(nrows=df['metric'].nunique(),
                              ncols=df['model'].nunique(),
                              sharex=True,
                              sharey=True,
                              figsize=(15, 5))

for (i, (ax, (mt, metrics))) in enumerate(zip(axes, df.groupby('metric'))):
    iterable = zip(ax, metrics.groupby('model'))
    for (j, (cell, (mo, models))) in enumerate(iterable):
        sns.pointplot(x='ngrams',
                      y='value',
                      data=models,
                      order=sorted(models['ngrams'].unique()),
                      ax=cell)
        if not j:
            cell.set_ylabel(mt)
        else:
            cell.set_ylabel('')
        if not i:
            cell.set_title(mo)
        cell.set_xlabel('')
        cell.grid(True, which='both', axis='y', linestyle='dashed')
plt.savefig(str(args.output), bbox_inches='tight')
