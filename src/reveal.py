import csv
import itertools
from pathlib import Path
from argparse import ArgumentParser
from collections import defaultdict
from multiprocessing import Pool

import numpy as np
import pandas as pd

import zrtlib.selector.technique as tek
import zrtlib.selector.strategy as strat
from zrtlib import indri
from zrtlib import logger
from zrtlib import zutils
from zrtlib.query import QueryBuilder
from zrtlib.indri import QueryDoc, QueryExecutor, TrecMetric
from zrtlib.document import TermDocument, HiddenDocument
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
arguments.add_argument('--retrieval-model')
arguments.add_argument('--selection-strategy')
arguments.add_argument('--feedback-metric')
arguments.add_argument('--seed', default='')
arguments.add_argument('--index', type=Path)
arguments.add_argument('--query', type=Path)
arguments.add_argument('--qrels', type=Path)
arguments.add_argument('--input', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--replay', type=Path, action='append')
arguments.add_argument('--guesses', type=int, default=np.inf)
args = arguments.parse_args()

log = logger.getlogger()

#
# Initialise the query and the selector
#
query = HiddenDocument(args.query)

if args.selection_strategy == 'relevance':
    relevant = set(indri.relevant_documents(args.qrels))
    st = strat.BlindHomogenous(tek.Relevance, query=query, relevant=relevant)
elif args.selection_strategy == 'direct':
    feedback = RecentWeighted()
    st = strat.DirectNeighbor(feedback=feedback,
                              radius=5,
                              technique=tek.Entropy)
elif args.selection_strategy == 'nearest':
    feedback = RecentWeighted()
    st = strat.NearestNeighbor(feedback=feedback,
                               radius=5,
                               technique=tek.Entropy)
else:
    technique = {
        'tf': tek.TermFrequency,
        'df': tek.DocumentFrequency,
        'random': tek.Random,
        'entropy': tek.Entropy,
    }
    st = strat.BlindHomogenous(technique[args.selection_strategy])

ts = TermSelector(st)
with Pool() as pool:
    iterable = itertools.filterfalse(QueryDoc.isquery, zutils.walk(args.input))
    for i in pool.imap_unordered(TermDocument, iterable):
        ts.add(i)

#
# Establish the metric of interest
#
eval_metric = TrecMetric(args.feedback_metric)

#
# Begin revealing
#
with CSVWriter(args.query.stem, args.output) as writer:
    with QueryExecutor(args.index, args.qrels) as engine:
        for (i, term) in enumerate(itertools.chain(args.seed, ts), 1):
            if i > args.guesses or not query:
                log.debug('Guessing finished')
                break

            #
            # Flip the term
            #
            flipped = query.flip(term)
            log.info('g {0} {1} {2}'.format(i, term, flipped))
            if not flipped:
                continue

            #
            # Run the query and evaluate
            #
            engine.query(QueryBuilder(args.retrieval_model, query))
            (_, evaluation) = next(engine.evaluate(eval_metric))

            #
            # Collect and record the results
            #
            results = {
                'guess': i,
                'term': term,
                'hidden': float(query),
                **evaluation,
            }
            writer.writerow(results)

            #
            # Report back to the term selector
            #
            ts.feedback = results[repr(eval_metric)]
            log.info('f {0} {1}'.format(eval_metric.metric, ts.feedback))
