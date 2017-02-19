import collections
import operator as op
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

import numpy as np
import pandas as pd
import seaborn as sns

from zrtlib import logger
from zrtlib import zutils
from zrtlib.document import TermDocument

def func(args):
    (document, keys) = args

    log = logger.getlogger()

    counter = collections.Counter()
    terms = TermDocument(document)
    ngrams = int(document.parent.stem)

    log.info('{0} {1}'.format(*document.parts[-2:]))

    for row in terms.df.itertuples():
        counter.update(zutils.count(row.start, row.end))

    return [ dict(zip(keys, (*x, ngrams))) for x in counter.items() ]

def aquire(term_files, columns):
    with Pool() as pool:
        iterable = map(lambda x: (x, list(columns)), args.term_file)
        for i in pool.imap(func, iterable):
            yield from i

arguments = ArgumentParser()
arguments.add_argument('--term-file', type=Path, action='append')
arguments.add_argument('--start', type=int, default=0)
arguments.add_argument('--end', type=float, default=np.inf)
args = arguments.parse_args()

log = logger.getlogger()

columns = collections.OrderedDict([
    ('time', 'location'),
    ('value', 'active'),
    ('condition', 'n-grams'),
])

df = pd.DataFrame(aquire(args.term_file, columns.values()))
df = df[(df.location >= args.start) & (df.location <= args.end)]

log.info('Plotting')

sns.set_context('paper')
markers = [ None ] * len(args.term_file)
ax = sns.tsplot(data=df, err_style=None, unit=columns['condition'], **columns)
ax.set(ylim=(0, None))

potentials = set(map(op.attrgetter('stem'), args.term_file))
fname = potentials.pop()
assert(len(potentials) == 0)
ax.figure.savefig(fname + '.png', bbox_inches='tight')
