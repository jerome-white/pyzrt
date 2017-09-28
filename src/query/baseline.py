import csv
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser

from zrtlib import logger
from zrtlib.indri import QueryDoc, QueryExecutor, TrecMetric
from zrtlib.jobqueue import JobQueue

def func(incoming, outgoing, args):
    log = logger.getlogger()
    metrics = map(TrecMetric, args.feedback_metric)

    while True:
        query = incoming.get()
        log.info(query.stem)

        results = { 'topic': QueryDoc.components(query).topic }
        judgements = args.qrels.joinpath(results['topic'])
        with QueryExecutor(args.index, judgements, True) as engine:
            engine.query(query.read_text())
            (_, evaluation) = next(engine.evaluate(*metrics))
        results.update(evaluation)

        outgoing.put(results)

arguments = ArgumentParser()
arguments.add_argument('--index', type=Path)
arguments.add_argument('--query', type=Path)
arguments.add_argument('--qrels', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--feedback-metric', action='append', default=[])
args = arguments.parse_args()

log = logger.getlogger()

incoming = mp.Queue()
outgoing = mp.Queue()

with mp.Pool(initializer=func, initargs=(outgoing, incoming, args)):
    results = []
    fieldnames = set()
    queue = JobQueue(incoming, outgoing, args.query.iterdir())

    for i in queue:
        fieldnames.update(i.keys())
        results.append(i)

    with args.output.open('w') as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
