import csv
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser

from zrtlib import logger
from zrtlib.indri import QueryDoc, QueryExecutor

class JobQueue:
    def __init__(self, incoming, outgoing, jobs):
        self.incoming = incoming
        self.outgoing = outgoing
        self.job_count = 0

        for i in jobs:
            self.outgoing.put(i)
            self.job_count += 1

    def __iter__(self):
        return self

    def __next__(self):
        if not self.job_count:
            raise StopIteration

        item = self.incoming.get()
        self.job_count -= 1

        return item

def func(incoming, outgoing, args):
    metrics = map(TrecMetric, args.feedback_metrics)

    with QueryExecutor(args.index, args.qrels) as engine:
        while True:
            query = incoming.get()

            results = { 'topic': QueryDoc.components(query).topic }
            with query.open() as fp:
                engine.query(fp.read())
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
    queue = JobQueue(incoming, outgoing, args.query.iterdir())

    with args.output('w') as fp:
        writer = None
        for i in queue:
            if writer is None:
                writer = csv.DictWriter(fp, fieldnames=i.keys())
                writer.writeheader()
            writer.writerow(i)
