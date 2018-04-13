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

sns.set_context('paper', rc={'lines.linewidth': 1})
# sns.set(font_scale=1.7)
sns.set_style('whitegrid', {
    'lines.solid_capstyle': 'butt',
})

g = sns.FacetGrid(df, row='metric', col='model', sharex=False)
g.map(sns.pointplot,
      'ngrams',
      'value',
      order=sorted(df['ngrams'].unique()),
      markers=',',
      errwidth=1)

for ((row, col, _), data) in g.facet_data():
    ax = g.facet_axis(row, col)

    if not col:
        ax.set_ylabel(data['metric'].unique().item())
    ax.set_title('' if row else data['model'].unique().item())

    ylim = max(map(abs, ax.get_ylim()))
    ax.set_ylim(-ylim, ylim)

    ax.axhline(color='r')

sns.despine(left=True)

g.savefig(str(args.output), bbox_inches='tight')
