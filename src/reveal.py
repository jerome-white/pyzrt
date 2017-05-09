import io
import csv
import itertools
import functools
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

class Picker:
    def terms(self):
        raise NotImplementedError()

    def add(self, term):
        raise NotImplementedError()

    def __bool__(self):
        return False

class HiddenQuery(Picker):
    def __init__(self, hidden_document):
        self.document = hidden_document

    def terms(self):
        return self.document

    def add(self, term):
        return self.document.flip(term) > 0

    def __float__(self):
        return float(self.document)

    def __bool__(self):
        return bool(self.document)

class ProgressiveQuery(Picker):
    def __init__(self):
        self.df = pd.DataFrame()

    def add(self, term):
        self.df = self.df.append(term, ignore_index=True)
        return True

    def terms(self):
        return TermDocument(io.StringIO(self.df.to_csv(index=False)))

    def __float__(self):
        return float(len(self.df))

arguments = ArgumentParser()
arguments.add_argument('--retrieval-model')
arguments.add_argument('--selection-strategy')
arguments.add_argument('--sieve')
arguments.add_argument('--feedback-metric')
arguments.add_argument('--clusters', type=Path)
arguments.add_argument('--index', type=Path)
arguments.add_argument('--query', type=Path)
arguments.add_argument('--qrels', type=Path)
arguments.add_argument('--input', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--seed', action='append', default=[])
arguments.add_argument('--guesses', type=int, default=np.inf)
args = arguments.parse_args()

log = logger.getlogger()

#
# Initialise the query and the selector
#
document = HiddenDocument(args.query)
ss = args.selection_strategy
if ss == 'relevance':
    relevant = set(indri.relevant_documents(args.qrels))
    technique = functools.partial(tek.Relevance,
                                  query=document,
                                  relevant=relevant)
    st = strat.BlindHomogenous(technique)
elif ss == 'direct' or ss == 'nearest' or ss == 'feedback':
    strategy = {
        'direct': strat.DirectNeighbor,
        'nearest': strat.NearestNeighbor,
        'feedback': strat.BlindRelevance,
    }[ss]
    sieve = {
        'cluster': functools.partial(ClusterSieve, args.clusters),
        'term' : TermSieve,
    }[args.sieve]()
    technique = functools.partial(tek.Entropy)

    st = strategy(sieve, technique)
else:
    options = {
        'tf': tek.TermFrequency,
        'df': tek.DocumentFrequency,
        'random': tek.Random,
        'entropy': tek.Entropy,
    }
    technique = functools.partial(options[ss])
    st = strat.BlindHomogenous(technique)

ts = TermSelector(st, RecentWeighted(), args.seed)
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
        query = HiddenQuery(document)
        for (i, term) in enumerate(ts, 1):
            if i > args.guesses or not query:
                log.debug('Guessing finished')
                break

            #
            # Add the term to the query
            #
            added = query.add(term)
            log.info('g {0} {1} {2}'.format(i, term))
            if not added:
                ts.feedback.append(0)
                continue

            #
            # Run the query and evaluate
            #
            engine.query(QueryBuilder(args.retrieval_model, query.terms()))
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
            ts.feedback.append(results[repr(eval_metric)])
            log.info('f {0} {1}'.format(eval_metric.metric, ts.feedback))
