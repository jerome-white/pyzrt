import csv
import itertools
from pathlib import Path
from argparse import ArgumentParser
from collections import defaultdict
from multiprocessing import Pool

import numpy as np

from zrtlib import logger
from zrtlib import zutils
from zrtlib.query import QueryBuilder
from zrtlib.indri import QueryDoc, QueryExecutor
from zrtlib.selector import Selector
from zrtlib.document import TermDocument, HiddenDocument

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
arguments.add_argument('--input', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--count', type=int, default=1000)
arguments.add_argument('--guesses', type=int, default=np.inf)
args = arguments.parse_args()

log = logger.getlogger()

#
# Initialise the query and the selector
#
query = HiddenDocument(args.query)
terms = Selector(args.selector)

with Pool() as pool:
    iterable = itertools.filterfalse(QueryDoc.isquery, zutils.walk(args.input))
    for i in pool.imap_unordered(TermDocument, iterable):
        terms.add(i)

try:
    # Divulge relevance information to oracles
    terms.divulge(args.qrels, query)
except NotImplementedError:
    pass

#
# Begin revealing
#
with CSVWriter(args.output) as writer, QueryExecutor(args.index) as engine:
    results = {}

    predicate = lambda x: x[0] < args.guesses
    for i in itertools.takewhile(predicate, enumerate(terms)):
        #
        # Turn it over
        #
        flipped = query.flip(i)
        log.info('{0}: {1}'.format(i, flipped))
        if not flipped:
            continue

        results['guess'] = i
        results['term'] = i

        #
        # Run the query
        #
        q = QueryBuilder(args.model, query)
        result = engine.query(q, args.count)

        #
        # Collect the results
        #
        collect = defaultdict(list)

        for entry in engine.evaluate(args.qrels):
            for (metric, value) in entry:
                collect[metric].append(value)

        if collect:
            f = np.mean
        else:
            log.error('No values obtained')
            f = lambda x: np.nan
        results.update({ x: f(y) for (x, y) in collect })

        #
        # Record
        #
        writer.writerow(results)
