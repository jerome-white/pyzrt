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
from zrtlib import indri
from zrtlib.query import QueryBuilder
from zrtlib.indri import QueryDoc, QueryExecutor, TrecMetric
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
arguments.add_argument('--retrieval-model')
arguments.add_argument('--selection-strategy')
arguments.add_argument('--feedback-metric')
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
    kwargs = {
        'query': query,
        'relevant': set(indri.relevant_documents(args.qrels)),
    }
else:
    kwargs = {}

ts = TermSelector(SelectionStrategy.build(args.selection_strategy, **kwargs))
with Pool() as pool:
    iterable = itertools.filterfalse(QueryDoc.isquery, zutils.walk(args.input))
    for i in pool.imap_unordered(TermDocument, iterable):
        ts.add(i)

#
# Establish the metric of interest
#
eval_metric = TrecMetric(args.feedback_metric)

#
# Load the data in the event that there are logs to replay
#
guesses = []
if args.replay:
    for i in args.replay:
        with i.open() as fp:
            for (instruction, *actions) in logger.readlog(fp, True):
                if instruction == 'g':
                    (guess, term, flipped) = actions
                    f = query.flip(term)
                    assert(f == int(flipped))
                    guesses.append(int(guess))
                    ts.mark_selected(term, guesses[-1])
                elif instruction == 'f':
                    (metric, value) = actions
                    assert(metric == str(eval_metric))
                    ts.feedback = float(value)
                else:
                    log.error('unknown instruction {1}'.format(instruction))
initial = max(guesses) if guesses else 0

#
# Begin revealing
#
with CSVWriter(args.output) as writer:
    with QueryExecutor(args.index, args.qrels) as engine:
        for (i, term) in enumerate(ts, initial + 1):
            if i > args.guesses or not query:
                break

            #
            # Flip the term
            #
            flipped = query.flip(term)
            log.info('g {0} {1} {2}'.format(i, term, len(flipped)))
            if flipped.empty:
                continue

            #
            # Run the query and evaluate
            #
            engine.query(QueryBuilder(args.retrieval_model, query))
            evaluation = engine.evaluate(eval_metric)

            #
            # Collect and record the results
            #
            results = {
                'guess': i,
                'term': term,
                **next(evaluation),
            }
            writer.writerow(results)

            #
            # Report back to the term selector
            #
            ts.feedback = results[repr(eval_metric)]
            log.info('f {0} {1}'.format(eval_metric, ts.feedback))
