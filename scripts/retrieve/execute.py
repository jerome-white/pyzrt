import csv
import collections as cl
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser

import pyzrt as pz

Info = cl.namedtuple('Info', 'model, topic, ngrams')

def func(queue, index, feedback):
    log = pz.util.get_logger()

    metrics = map(pz.TrecMetric, feedback)

    while True:
        (query, output, qrels, info) = queue.get()
        log.info('{0}'.format(query.name))

        relevance = pz.QueryRelevance(qrels)
        search = pz.Search(index, relevance)
        writer = None

        with output.open('w') as fp:
            for i in search.do(query, metrics):
                entry = info._asdict()
                assert(not any([ x in i.results for x in entry ]))
                entry.update(**i.results)

                if writer is None:
                    writer = csv.DictWriter(fp, fieldnames=entry.keys())
                    writer.writeheader()
                writer.writerow(entry)

        if not output.stat().st_size:
            log.warning('{0} x'.format(query.name))
            output.unlink()

        queue.task_done()

arguments = ArgumentParser()
arguments.add_argument('--index', type=Path)
arguments.add_argument('--qrels', type=Path)
arguments.add_argument('--queries', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--feedback-metric', action='append', default=[])
arguments.add_argument('--ngrams', type=int)
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
args = arguments.parse_args()

log = pz.util.get_logger(True)

queue = mp.JoinableQueue()
initargs = [
    queue,
    args.index,
    args.feedback_metric,
]

log.info('++ begin {0}'.format(args.queries))
with mp.Pool(args.workers, func, initargs) as pool:
    for i in args.queries.iterdir():
        out = args.output.joinpath(i.name)
        if not out.exists():
            components = pz.TrecDocument.components(i)

            qrels = args.qrels.joinpath(str(components.topic))
            model = i.suffix[1:] # without the '.'
            info = Info(model, components.topic, args.ngrams)

            queue.put((i, out, qrels, info))
    queue.join()
log.info('-- end')
