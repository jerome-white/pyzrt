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

def aquire(args, columns):
    df = TermDocument(args.term_file).df
    df = df[(df.start >= args.start) & (df.start <= args.end)]

    for (i, row) in enumerate(df.itertuples(), 1):
        for j in ('start', 'end'):
            f = op.attrgetter(j)
            yield dict(zip(columns, (f(row), i)))

arguments = ArgumentParser()
arguments.add_argument('--term-file', type=Path)
arguments.add_argument('--start', type=int, default=0)
arguments.add_argument('--end', type=float, default=np.inf)
args = arguments.parse_args()

log = logger.getlogger()

columns = collections.OrderedDict([
    ('x', 'location'),
    ('y', 'term'),
#    ('hue', '_')
])
# columns['hue'] = columns['x']

df = pd.DataFrame(aquire(args, columns.values()))

log.info('Plotting')

sns.set_context('paper')
sns.set(font_scale=1.7)
sns.set_palette(sns.color_palette('Blues'))

ax = sns.pointplot(data=df, ci=None, hue=columns['y'], **columns)
ax.set(xticks=np.linspace(df.location.min(), df.location.max(), 5),
       ylim=(0, None))
ax.legend().remove()

fname = 'overlap-{0}.png'.format(args.term_file.stem)
log.info(fname)
ax.figure.savefig(fname, bbox_inches='tight')
