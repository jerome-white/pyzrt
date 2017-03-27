import csv
from pathlib import Path
from argparse import ArgumentParser

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

arguments = ArgumentParser()
arguments.add_argument('--metric')
arguments.add_argument('--input', type=Path)
args = arguments.parse_args()

index = 'guess'
usecols = [
    index,
    args.metric,
]

df = pd.read_csv(str(args.input),
                 index_col=usecols.index(index),
                 usecols=usecols)
df = (df.
      reindex(range(df.index.min(), df.index.max()), method='ffill').
      reset_index().
      assign(**dict(zip(('strategy', 'topic'), args.input.parts[-2:])))
)

plt.figure(figsize=(24, 6))
# sns.set_context('paper')
sns.set(font_scale=1.7)
ax = sns.pointplot(x=index,
                   y=args.metric,
                   hue='strategy',
                   data=df,
                   markers='')
ax.set(ylim=(0, None),
       ylabel=args.metric)
ax.figure.savefig('flips.png', bbox_inches='tight')
