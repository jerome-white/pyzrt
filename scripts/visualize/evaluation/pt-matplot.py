import sys
import operator as op
import collections as cl
from pathlib import Path
from argparse import ArgumentParser

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

Element = cl.namedtuple('Element', 'name, order, ax, df')

def each(axes, group):
    for (a, (b, (c, d))) in enumerate(zip(axes, group)):
        yield Element(c, a, b, d)

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

for i in each(axes, df.groupby('metric')):
    for j in each(i.ax, i.df.groupby('model')):
        sns.pointplot(x='ngrams',
                      y='value',
                      data=j.df,
                      order=sorted(j.df['ngrams'].unique()),
                      ax=j.ax)

        ylabel = '' if j.order else i.name
        j.ax.set_ylabel(ylabel)
        j.ax.set_xlabel('')

        if not i:
            j.ax.set_title(j.name)

        j.ax.grid(True, which='both', axis='y', linestyle='dashed')
plt.savefig(str(args.output), bbox_inches='tight')
