import csv
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser

import pyzrt as pz

def func(queue, index, qrels, feedback):
    log = pz.util.get_logger()

    metrics = map(pz.TrecMetric, feedback)
    relevance = pz.QueryRelevance(qrels)
    search = pz.Search(index, relevance)

    while True:
        (query, output) = queue.get()
        log.info('{0}'.format(query.name))

        info = pz.TrecDocument.components(query)
        model = query.suffix[1:] # without the '.'

        with output.open('w') as fp:
            writer = None
            for record in search.do(query, metrics):
                entry = { 'model': model, 'topic': info.topic }
                assert(not any([ x in record for x in entry ]))
                entry.update(**record)

                if writer is None:
                    writer = csv.DictWriter(fp, fieldnames=entry.keys())
                    writer.writeheader()
                writer.writerow(entry)

        queue.task_done()

arguments = ArgumentParser()
arguments.add_argument('--index', type=Path)
arguments.add_argument('--qrels', type=Path)
arguments.add_argument('--queries', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--feedback-metric', action='append', default=[])
arguments.add_argument('--workers', type=int)
args = arguments.parse_args()

log = pz.util.get_logger(True)

queue = mp.JoinableQueue()
initargs = [
    queue,
    args.index,
    args.qrels,
    args.feedback,
]

log.info('++ begin {0}'.format(args.term_files))
with mp.Pool(args.workers, func, initargs) as pool:
    for i in args.queries.iterdir():
        out = args.output.joinpath(i.name)
        if not out.exists():
            queue.put(i, out)
    queue.join()
log.info('-- end')
