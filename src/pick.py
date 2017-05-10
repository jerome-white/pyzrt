import csv
import itertools
import functools
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

import numpy as np

import zrtlib.selector.technique as tq
import zrtlib.selector.strategy as st
import zrtlib.selector.sieve as sv
from zrtlib import indri
from zrtlib import logger
from zrtlib import zutils
from zrtlib.query import QueryBuilder
from zrtlib.indri import QueryDoc, QueryExecutor, TrecMetric
from zrtlib.document import TermDocument
from zrtlib.selector.picker import ProgressiveQuery
from zrtlib.selector.feedback import RecentWeighted
from zrtlib.selector.management import TermSelector

class CSVWriter:
    def __init__(self, query, path):
        self.writer = None

        q = query
        while True:
            fname = path.joinpath(q)
            if not fname.exists():
                self.fp = fname.open('w', buffering=1)
                break
            (name, number) = q.split(QueryDoc.separator)
            n = str(int(number) + 1).zfill(len(number))
            assert(len(n) <= len(number))
            q = QueryDoc.separator.join([ name, n ])

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

arguments.add_argument('--strategy')
arguments.add_argument('--technique')
arguments.add_argument('--sieve')
arguments.add_argument('--feedback-level', type=int, default=2)

arguments.add_argument('--index', type=Path)
arguments.add_argument('--qrels', type=Path)
arguments.add_argument('--input', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--clusters', type=Path)

arguments.add_argument('--seed', action='append', default=[])
arguments.add_argument('--guesses', type=int, default=np.inf)
args = arguments.parse_args()

log = logger.getlogger()

#
# Feedback
#

feedback = RecentWeighted(args.feedback_level)

#
# Technique
#

technique = functools.partial({
    'tf': tq.TermFrequency,
    'df': tq.DocumentFrequency,
    'random': tq.Random,
    'entropy': tq.Entropy,
}[args.technique])

#
# Sieve
#

sieve = {
    'cluster': functools.partial(sv.ClusterSieve, args.clusters),
    'term' : sv.TermSieve,
}[args.sieve]()

#
# Strategy
#

strategy = {
    'direct': st.DirectNeighbor,
    'nearest': st.NearestNeighbor,
    'feedback': st.BlindRelevance,
}[args.selection-strategy](sieve, technique)

#
# Selection manager
#

manager = TermSelector(strategy, feedback, args.seed)

with Pool() as pool:
    iterable = itertools.filterfalse(QueryDoc.isquery, zutils.walk(args.input))
    for i in pool.imap_unordered(TermDocument, iterable):
        manager.add(i)

#
# Metric
#
eval_metric = TrecMetric(args.feedback_metric)

#
# Begin the game!
#

with CSVWriter(args.query.stem, args.output) as writer:
    with QueryExecutor(args.index, args.qrels) as engine:
        query = ProgressiveQuery()
        for (i, term) in enumerate(manager, 1):
            if i > args.guesses or not query:
                log.debug('Guessing finished')
                break

            #
            # Add the term to the query
            #
            added = query.add(term)
            log.info('g {0} {1} {2}'.format(i, term))
            if not added:
                manager.feedback.append(0)
                continue

            #
            # Run the query and evaluate
            #
            engine.query(QueryBuilder(query.terms()))
            (_, evaluation) = next(engine.evaluate(eval_metric))

            #
            # Collect and record the results
            #
            results = {
                'guess': i,
                'term': term,
                'progress': float(query),
                **evaluation,
            }
            writer.writerow(results)

            #
            # Report back to the term selector
            #
            manager.feedback.append(results[repr(eval_metric)])
            log.info('f {0} {1}'.format(eval_metric.metric, manager.feedback))
