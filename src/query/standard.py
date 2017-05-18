import csv
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

from zrtlib import zutils
from zrtlib import logger
from zrtlib.query import QueryBuilder
from zrtlib.indri import QueryExecutor, QueryDoc, TrecMetric
from zrtlib.document import TermDocument

def func(args):
    (terms, options) = args

    log = logger.getlogger()

    model_key = 'model'
    rows = []
    fieldnames = set()

    document = TermDocument(terms)
    metrics = map(TrecMetric, options.feedback_metric)
    qrels = options.qrels.joinpath(QueryDoc.components(terms).topic)

    with QueryExecutor(options.index, qrels) as engine:
        for i in options.models:
            log.info('{0} {1}'.format(terms.stem, i))

            engine.query(QueryBuilder(document, i))
            (_, evaluation) = next(engine.evaluate(*metrics))

            assert(model_key not in evaluation)
            results = { model_key: i, **evaluation }
            fieldnames.update(results.keys())
            rows.append(results)

    output = options.output.joinpath(terms.stem).with_suffix('.csv')
    with output.open('w', buffering=1) as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return terms

arguments = ArgumentParser()
arguments.add_argument('--index', type=Path)
arguments.add_argument('--qrels', type=Path)
arguments.add_argument('--term-files', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--model', action='append')
arguments.add_argument('--feedback-metric', action='append', default=[])
args = arguments.parse_args()

assert(args.model)

log = logger.getlogger()

with Pool() as pool:
    iterable = filter(QueryDoc.isquery, zutils.walk(args.term_files))
    for i in pool.imap(func, map(lambda x: (x, args), iterable)):
        log.info(i.stem)
