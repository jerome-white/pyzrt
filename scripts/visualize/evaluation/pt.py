import sys
from pathlib import Path
from argparse import ArgumentParser

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

import pyzrt as pz

arguments = ArgumentParser()
arguments.add_argument('--output', type=Path)
arguments.add_argument('--metric', action='append')
arguments.add_argument('--min-relevant', type=int, default=0)
args = arguments.parse_args()

metric_label = {
    'map': 'MAP',
    'recip_rank': 'Mean Reciprocal Rank',
    'ndcg': 'NDCG',
}
metrics = [ repr(pz.TrecMetric(x)) for x in args.metric ]

df = pd.read_csv(sys.stdin)
df = (df[df['num_rel'] >= args.min_relevant]
      .melt(id_vars=['model', 'ngrams'],
            value_vars=metrics,
            var_name='metric',
            value_name='value')
      .sort_values(by=['metric', 'model', 'ngrams']))

# sns.set_context('paper')
#sns.set(font_scale=1.7)
sns.set_style('whitegrid')

g = sns.FacetGrid(df, row='metric', col='model')
g.map(sns.pointplot, 'ngrams', 'value')

g.savefig(str(args.output), bbox_inches='tight')
