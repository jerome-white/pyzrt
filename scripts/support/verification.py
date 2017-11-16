# Verify that UA queries from homogenous n-gram windows are equivalent
# to their English counterparts

import sys
import itertools as it
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

from zrtlib import logger
from zrtlib.document import TermDocument

def func(args):
    (topic, en, pt) = args

    log = logger.getlogger()

    err = None
    words = en.joinpath(topic).read_text().split()
    terms = TermDocument(pt.joinpath(topic))

    for (i, j) in it.zip_longest(words, terms.df['ngram'].values):
        if i is None or j is None:
            err = '{0}: ngram counts'.format(topic)
            break

        original = i.replace('_', ' ')
        if original != j:
            err = '{0}: ngram difference {1} {2}'.format(topic, original, j)
            break

    result = [topic]
    if err is not None:
        log.error(err)
        result.append('*')

    return ' '.join(result)

arguments = ArgumentParser()
arguments.add_argument('--english', type=Path)
arguments.add_argument('--pseudoterms', type=Path)
args = arguments.parse_args()

with Pool() as pool:
    log = logger.getlogger()

    # There should be an equivalent number
    (en, pt) = [ set(x.iterdir()) for x in (args.english, args.pseudoterms) ]
    if len(en.symmetric_difference(pt)) == 0:
        log.error('Number of topics differ')
        sys.exit()

    iterable = map(lambda x: (x.stem, args.english, args.pseudoterms), en)
    for i in pool.imap_unordered(func, iterable):
        log.info(i)
