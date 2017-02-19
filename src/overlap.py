import collections
import operator as op
from pathlib import Path
from argparse import ArgumentParser

import numpy as np
import pandas as pd
import seaborn as sns

from zrtlib import zutils
from zrtlib.document import TermDocument

def func(document):
    counter = collections.Counter()    
    terms = TermDocument(document)
    ngrams = int(document.parent.stem)    

    for row in terms.df.itertuples():
        counter.update(zutils.count(row.start, row.end))

    return [ (*x, ngrams) for x in counter.items() ]

arguments = ArgumentParser()
arguments.add_argument('--term-file', type=Path, action='append')
arguments.add_argument('--start', type=int, default=0)
arguments.add_argument('--end', type=float, default=np.inf)
args = arguments.parse_args()

columns = collections.OrderedDict([
    ('x', 'location'),
    ('y', 'count'),
    ('hue', 'n-grams'),
])
for Pool() as pool:
    df = pd.DataFrame(pool.imap(func, term_file), columns=columns.values())
df = df[(df.location >= args.start) & (df.location <= args.end)]

sns.set_context('paper')
ax = plotter(data=df, markers=None, **columns)

potentials = list(map(op.attrgetter('stem'), args.term_file))
fname = potentials.pop()
assert(len(potentials) == 0)
ax.figure.savefig(fname + '.png', bbox_inches='tight')
