import os
import csv
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile
from collections import defaultdict

from zrtlib import zutils
from zrtlib import logger
from zrtlib.query import QueryBuilder
from zrtlib.indri import QueryExecutor, QueryDoc, TrecMetric
from zrtlib.document import TermDocument, StandardDocument

def log_error(engine, errdir):
    p = Path(errdir, '.pyzrt', 'errors')
    p.mkdir(parents=True, exist_ok=True)

    with NamedTemporaryFile(mode='w', delete=False, dir=str(p)) as fp:
        dest = fp.name
    engine.saveq(dest)

    return dest

def func(feedback, qrels, index, output, queue):
    log = logger.getlogger()

    metrics = map(TrecMetric, feedback)

    while True:
        (terms, model) = queue.get()
        log.info('{0} {1}'.format(terms.stem, model))

        if model == 'baseline':
            document = StandardDocument(terms)
        else:
            document = TermDocument(terms)

        relevance = qrels.joinpath(QueryDoc.components(terms).topic)

        with QueryExecutor(index, relevance) as engine:
            engine.query(QueryBuilder(document, model))
            try:
                (_, evaluation) = next(engine.evaluate(*metrics))

                record = { 'model': model, 'query': terms.stem }
                assert(not any([ x in evaluation for x in record.keys() ]))
                record.update(**evaluation)

                with NamedTemporaryFile(mode='w',
                                        suffix='.csv',
                                        delete=False,
                                        dir=output) as fp:
                    writer = csv.DictWriter(fp, fieldnames=record.keys())
                    writer.writeheader()
                    writer.writerow(record)
                    path = Path(fp.name)
                engine.saveq(path.with_suffix('.query'))
            except ValueError:
                msg = '{0} {1}'.format(terms.stem, model)

                errdir = 'HOME'
                if errdir in os.environ:
                    msg += ': ' + log_error(engine, os.environ[errdir])

                log.error(msg)

        queue.task_done()

def each(args):
    log = logger.getlogger()

    seen = defaultdict(set)

    for i in args.output.iterdir():
        if not i.suffix('.csv'):
            continue

        with i.open() as fp:
            for line in csv.DictReader(fp):
                (m, q) = [ line[x] for x in ('model', 'query') ]
                seen[q].add(m)

    for model in args.model:
        for query in filter(QueryDoc.isquery, zutils.walk(args.term_files)):
            q = query.stem
            if q in seen and model in seen[q]:
                log.warning('* {0} {1}'.format(q, model))
            else:
                yield (query, model)

arguments = ArgumentParser()
arguments.add_argument('--index', type=Path)
arguments.add_argument('--qrels', type=Path)
arguments.add_argument('--term-files', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--model', action='append')
arguments.add_argument('--feedback-metric', action='append', default=[])
args = arguments.parse_args()

assert(args.model)

log = logger.getlogger(True)

queue = mp.JoinableQueue()
initargs = [
    args.feedback_metric,
    args.qrels,
    args.index,
    args.output,
    queue,
    ]

log.info('++ begin {0}'.format(args.term_files))
with mp.Pool(initializer=func, initargs=initargs) as pool:
    for i in each(args):
        queue.put(i)
    queue.join()
log.info('-- end')
