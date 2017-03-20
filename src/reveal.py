import csv
import itertools
from pathlib import Path
from argparse import ArgumentParser
from collections import defaultdict
from multiprocessing import Pool

import numpy as np
import pandas as pd

from zrtlib import logger
from zrtlib import zutils
from zrtlib.query import QueryBuilder
from zrtlib.indri import QueryDoc, QueryExecutor
from zrtlib.document import TermDocument, HiddenDocument
from zrtlib.selector import TermSelector, SelectionStrategy

class CSVWriter:
    def __init__(self, fname):
        self.fp = fname.open('w', buffering=1)
        self.writer = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.fp.close()

    def writerow(self, row):
        if self.writer is None:
            self.writer = csv.DictWriter(self.fp, fieldnames=row.keys())
            self. writer.writeheader()
        self.writer.writerow(row)

arguments = ArgumentParser()
arguments.add_argument('--model')
arguments.add_argument('--index')
arguments.add_argument('--selector')
arguments.add_argument('--query', type=Path)
arguments.add_argument('--qrels', type=Path)
arguments.add_argument('--corpus', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--depth', type=int, default=1000)
arguments.add_argument('--guesses', type=int, default=np.inf)
arguments.add_argument('--oracle', action='store_true')
args = arguments.parse_args()

log = logger.getlogger()

#
# Initialise the query and the selector
#
ts = TermSelector(SelectionStrategy.build(args.selector))
with Pool() as pool:
    iterable = itertools.filterfalse(QueryDoc.isquery, zutils.walk(args.input))
    for i in pool.imap_unordered(TermDocument, iterable):
        ts.add(i)

query = HiddenDocument(args.query)

#
# Begin revealing
#
with CSVWriter(args.output) as writer:
    with QueryExecutor(args.index, args.qrels) as engine:
        initial = 0
        recalled = pd.Series(initial, engine.relevants)

        if args.divulge:
            ts.divulge(recalled.index)

        for (i, term) in enumerate(ts, initial + 1):
            if i > args.guesses or recalled[recalled == initial].empty:
                break

            #
            # Flip the term
            #
            flipped = query.flip(term)
            log.info('{0}: {1}'.format(term, len(flipped)))
            if flipped.empty:
                continue

            #
            # Run the query
            #
            engine.query(QueryBuilder(args.model, query))

            #
            # Collect the results
            #
            recalled[engine.relevant()] = i

            ratio = recalled[recalled > initial].count() / recalled.count()
            results = {
                'guess': i,
                'term': term,
                'relevant': ratio,
            }
            results.update(dict(engine.evaluate()))

            #
            # Record
            #
            writer.writerow(results)

            #
            # Report back to the term selector
            #
            ts.feedback = recalled[recalled == i].index
