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
from zrtlib.indri import QueryDoc, QueryExecutor, relevant_documents
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
arguments.add_argument('--index')
arguments.add_argument('--retrieval-model')
arguments.add_argument('--selection-strategy')
arguments.add_argument('--feedback-metric')
arguments.add_argument('--query', type=Path)
arguments.add_argument('--qrels', type=Path)
arguments.add_argument('--input', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--guesses', type=int, default=np.inf)
args = arguments.parse_args()

log = logger.getlogger()

#
# Initialise the query and the selector
#
ts = TermSelector(SelectionStrategy.build(args.selection_strategy))
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
        for (i, term) in enumerate(ts, 1):
            if i > args.guesses:
                break

            #
            # Flip the term
            #
            flipped = query.flip(term)
            log.info('{0} {1} {2}'.format(i, term, len(flipped)))
            if flipped.empty:
                continue

            #
            # Run the query
            #
            engine.query(QueryBuilder(args.retrieval_model, query))

            #
            # Collect the results
            #
            results = {
                'guess': i,
                'term': term,
            }
            results.update(next(engine.evaluate()))

            #
            # Record
            #
            writer.writerow(results)

            #
            # Report back to the term selector
            #
            ts.feedback = results[args.feedback_metric]
