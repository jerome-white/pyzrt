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

arguments = ArgumentParser()
arguments.add_argument('--term-file', type=Path)
arguments.add_argument('--start', type=int, default=0)
arguments.add_argument('--end', type=float, default=np.inf)
args = arguments.parse_args()

log = logger.getlogger()

document = TermDocument(args.term_file)
df = document.df[['start', 'end']].reset_index().drop('index', axis=1)
df = df[(df.start >= args.start) & (df.start <= args.end)]
df /= df.max()
df.index += 1

sns.set_context('paper')
sns.set(font_scale=1.7)
sns.set_palette(sns.color_palette('Blues'))

for row in df.itertuples():
    plt.axhline(y=row.Index, xmin=row.start, xmax=row.end)

plt.xlim(df.start.min(), df.end.max())
plt.ylim(df.index[0] - 1, df.index[-1] + 1)
# plt.yticks([ 'T' + str(x) for x in plt.yticks()[1:-1] ])

# ax = sns.pointplot(data=df, ci=None, hue=columns['y'], **columns)
# ax.set(xticks=np.linspace(df.location.min(), df.location.max(), 5),
#        ylim=(0, None))
# ax.legend().remove()

fname = 'overlap-{0}.png'.format(args.term_file.stem)
log.info(fname)
plt.savefig(fname, bbox_inches='tight')
