import csv
# import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile

import numpy as np

from zrtlib import query
from zrtlib import logger
from zrtlib import zutils
from zrtlib.indri import QueryDoc, QueryExecutor
from zrtlib.document import HiddenDocument
from zrtlib.selector import RandomSelector
        
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
}[args.model]

log = logger.getlogger()
queries = {}
documents = RandomSelector()

for i in zutils.walk(args.input):
    log.info(i)

    doc = HiddenDocument(i)
    if QueryDoc.isquery(i):
        info = QueryDoc.components(i)
        queries[info.topic] = doc
    else:
        documents.add(doc)

with QueryExecutor() as query:
    with args.output.open('w') as fp:
        fieldnames = [ 'term' ] + list(queries.keys())
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()

        results = {}

        for term in documents:
            results['term'] = term
            changed = False

            for (topic, q) in queries.items():
                if q.flip(term) > 0:
                    changed = True
                    model = Model(q, **kwargs)

                    with NamedTemporaryFile(mode='w') as tmp:
                        tmp.write(str(model))
                        query.query(tmp.name, args.index, args.count)

                    values = []
                    qrels = args.qrels.joinpath(topic)                    
                    for line in query.evaluate(str(qrels), args.count):
                        (metric, run, value) = line.strip().split()
                        if run.isdigit() and metric == args.metric:
                            values.append(metric)
                    assert(values)
                    results[topic] = np.mean(values)

            if not args.compress_output or args.compress_output and changed:
                writer.writerow(results)

            if not any(queries.values()):
                break
