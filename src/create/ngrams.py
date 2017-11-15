#
# Parses a directory of files into term collection files. If
# max-gram's are specified, then the set will be of variable length
# (between min-gram and max-gram); it will be of constant size
# otherwise.
#
# Generally, files are assumed to have already been parsed;
# specifically, they are not in the TREC format.
#

import string
import itertools as it
import multiprocessing as mp
import collections as cl
from pathlib import Path
from argparse import ArgumentParser

from zrtlib import logger
from zrtlib import zutils
from zrtlib.terms import Term, TermCollection

def func(args):
    (document, output_directory, n, m) = args

    if m is None:
        m = n
    assert(0 < n <= m)

    window = cl.deque(maxlen=m)
    collection = TermCollection()

    log = logger.getlogger()
    log.info(document.stem)

    with document.open() as fp:
        for position in it.count():
            c = fp.read(1)
            if not c:
                break
            if c == ' ':
                c = '_'
            elif c in string.whitespace:
                continue

            window.append(c)

            if len(window) == window.maxlen:
                for i in range(n, m + 1):
                    for j in range(m - i + 1):
                        ngram = ''.join(it.islice(window, j, j + i))
                        term = Term(ngram, ngram, position - len(ngram))
                        collection.append(term)

    if collection:
        o = output_directory.joinpath(document.stem)
        with o.open('w') as fp:
            collection.tocsv(fp)
    else:
        log.warning(document.stem)

arguments = ArgumentParser()
arguments.add_argument('--documents', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--min-gram', type=int)
arguments.add_argument('--max-gram', type=int)
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
args = arguments.parse_args()

log = logger.getlogger(True)

log.info('>| begin')
with mp.Pool(args.workers) as pool:
    f = lambda x: (x, args.output, args.min_gram, args.max_gram)
    for _ in pool.imap_unordered(func, map(f, zutils.walk(args.documents))):
        pass
log.info('<| complete')
