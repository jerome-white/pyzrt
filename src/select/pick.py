import csv
import itertools
import functools as ft
from pathlib import Path
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile
from multiprocessing import Pool

import zrtlib.selector.technique as tq
import zrtlib.selector.strategy as st
import zrtlib.selector.sieve as sv
from zrtlib import logger
from zrtlib import zutils
from zrtlib.indri import QueryDoc, QueryExecutor, TrecMetric
from zrtlib.document import TermDocument
from zrtlib.selector.picker import ProgressiveQuery
from zrtlib.selector.feedback import RecentWeighted
from zrtlib.selector.management import TermSelector

#
# Arguments
#

arguments = ArgumentParser()

arguments.add_argument('--strategy')
arguments.add_argument('--technique')
arguments.add_argument('--sieve')
arguments.add_argument('--feedback-level', type=int, default=2)
arguments.add_argument('--feedback-metric')

arguments.add_argument('--index', type=Path)
arguments.add_argument('--documents', type=Path)
arguments.add_argument('--qrels', type=Path)
arguments.add_argument('--output-directory', type=Path)
arguments.add_argument('--clusters', type=Path)

arguments.add_argument('--seed', action='append', default=[])
arguments.add_argument('--guesses', type=int)
args = arguments.parse_args()

log = logger.getlogger()

#
# Feedback
#

feedback = RecentWeighted(args.feedback_level)

#
# Technique
#

technique = ft.partial({
    'tf': tq.TermFrequency,
    'df': tq.DocumentFrequency,
    'tfidf': tq.TFIDF,
    'random': tq.Random,
    'entropy': tq.Entropy,
}[args.technique])

#
# Sieve
#

if args.sieve == 'cluster':
    assert(args.clusters)

sieve = {
    'cluster': ft.partial(sv.ClusterSieve, args.clusters),
    'term' : sv.TermSieve,
}[args.sieve]()

#
# Strategy
#

strategy = {
    'direct': st.DirectNeighbor,
    'nearest': st.NearestNeighbor,
    'feedback': st.BlindRelevance,
}[args.strategy](sieve, technique)

#
# Selection manager
#

manager = TermSelector(strategy, feedback, args.seed)

with Pool() as pool:
    docs = zutils.walk(args.documents)
    iterable = itertools.filterfalse(QueryDoc.isquery, docs)
    for i in pool.imap_unordered(TermDocument, iterable):
        manager.add(i)

#
# Metric
#
eval_metric = TrecMetric(args.feedback_metric)

#
# Begin the game!
#
with NamedTemporaryFile(mode='w',
                        buffering=1,
                        dir=str(args.output_directory),
                        delete=False) as fp:
    writer = None
    query = ProgressiveQuery()

    with QueryExecutor(args.index, args.qrels) as engine:
        for (i, term) in enumerate(manager, 1):
            if args.guesses is not None and i > args.guesses:
                log.error('Maximum guesses reached')
                break

            #
            # Add the term to the query
            #
            try:
                added = query.add(term)
                log.info('g {0} {1} {2}'.format(i, term, added))
                if not added:
                    manager.feedback.append(0)
                    continue
            except BufferError:
                log.error('Query at capacity')
                break

            #
            # Run the query and evaluate
            #
            engine.query(query)
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
            if writer is None:
                writer = csv.DictWriter(fp, fieldnames=results.keys())
                writer.writeheader()
            writer.writerow(results)

            #
            # Report back to the term selector
            #
            manager.feedback.append(results[repr(eval_metric)])
            log.info('f {0} {1}'.format(eval_metric.metric, manager.feedback))
