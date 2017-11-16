import collections
import operator as op
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from zrtlib import logger
from zrtlib import zutils
from zrtlib.document import TermDocument

def aquire(args):
    keys = ('x', 'y')
    df = TermDocument(args.term_file).df
    df = df[(df.start >= args.start) & (df.start <= args.end)]

    for (i, row) in enumerate(df.itertuples(), 1):
        for j in ('start', 'end'):
            f = op.attrgetter(j)
            values = (f(row), i)
            yield dict(zip(keys, values))

arguments = ArgumentParser()
arguments.add_argument('--term-file', type=Path)
arguments.add_argument('--start', type=int, default=0)
arguments.add_argument('--end', type=float, default=np.inf)
arguments.add_argument('--save-data', type=Path)
args = arguments.parse_args()

log = logger.getlogger()

df = pd.DataFrame(aquire(args))

log.info('Plotting')

sns.set_context('paper')
sns.set(font_scale=1.7)
sns.set_palette(sns.color_palette(n_colors=1))

ax = None
groups = df.groupby('y')
for (_, grp) in groups:
    ax = grp.plot(x='x', y='y', ax=ax)

plt.ylim(0, len(groups) + 1)
plt.yticks(np.arange(*plt.ylim()),
           [ '' ] + list(range(1, len(groups) + 1)) + [ '' ])
plt.legend().remove()
plt.ylabel('Term')
plt.xlabel('Location')

fname = '{0}-overlap.png'.format(args.term_file.stem)
log.info(fname)
plt.savefig(fname, bbox_inches='tight')

if args.save_data:
    df.to_csv(args.save_data)
