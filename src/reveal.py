import csv
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile
from collections import namedtuple

import numpy as np

from zrtlib import query
from zrtlib import logger
from zrtlib import zutils
from zrtlib.indri import QueryDoc, QueryExecutor
from zrtlib.document import HiddenDocument
from zrtlib.selector import RandomSelector

QueryPackage = namedtuple('Query', 'topic, query')

def func(incoming, outgoing, opts):
    log = logger.getlogger()

    # XXX Should become a factory method in zrtlib.query
    (Model, kwargs) = {
        'ua': (query.BagOfWords, {}),
        'sa': (query.Synonym, {}),
        'u1': (query.Synonym, {
            'n_longest': 1,
        }),
        'un': (query.ShortestPath, {
            'partials': False,
        }),
        'uaw': (query.TotalWeight, {}),
        'saw': (query.LongestWeight, {}),
    }[opts.model]

    with QueryExecutor() as engine:
        while True:
            (job, payload) = incoming.get()

            if job == 'document':
                log.info('{0} {1}'.format(job, payload))

                if QueryDoc.isquery(payload):
                    info = QueryDoc.components(payload)
                    topic = info.topic
                else:
                    topic = None
                outgoing.put((topic, HiddenDocument(payload)))
            elif job == 'query':
                log.info('{0} {1}'.format(job, payload.topic))

                model = Model(payload.query, **kwargs)

                with NamedTemporaryFile(mode='w') as tmp:
                    tmp.write(str(model))
                    engine.query(tmp.name, opts.index, opts.count)

                values = []
                qrels = opts.qrels.joinpath(payload.topic)
                for line in engine.evaluate(str(qrels), args.count):
                    (metric, run, value) = line.strip().split()
                    if run.isdigit() and metric == args.metric:
                        values.append(metric)
                assert(values)

                outgoing.put((payload.topic, np.mean(values)))

arguments = ArgumentParser()
arguments.add_argument('--model')
arguments.add_argument('--index')
arguments.add_argument('--metric')
arguments.add_argument('--compress-output', action='store_true')
arguments.add_argument('--count', type=int, default=1000)
arguments.add_argument('--qrels', type=Path)
arguments.add_argument('--input', type=Path)
arguments.add_argument('--output', type=Path)
args = arguments.parse_args()

incoming = mp.Queue()
outgoing = mp.Queue()

with mp.Pool(initializer=func, initargs=(outgoing, incoming, args)):
    #
    #
    #
    queries = {}
    documents = RandomSelector()

    jobs = 0
    for i in zutils.walk(args.input):
        outgoing.put(('document', i))
        jobs += 1

    for _ in range(jobs):
        (topic, doc) = incoming.get()
        if topic is None:
            documents.add(doc)
        else:
            queries[topic] = doc

    #
    #
    #
    with args.output.open('w') as fp:
        fieldnames = [ 'term' ] + list(queries.keys())
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()

        results = {}

        for term in documents:
            changed = 0
            results['term'] = term

            for i in queries.items():
                package = QueryPackage(*i)
                if package.query.flip(term) > 0:
                    outgoing.put(('query', package))
                    changed += 1

            for _ in range(changed):
                (topic, value) = incoming.get()
                results[topic] = value

            if not args.compress_output or args.compress_output and changed:
                writer.writerow(results)

            if not any(queries.values()):
                break
