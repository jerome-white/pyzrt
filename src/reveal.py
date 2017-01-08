import csv
import itertools
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile

import numpy as np

from zrtlib import logger
from zrtlib import zutils
from zrtlib.query import QueryBuilder
from zrtlib.indri import QueryDoc, QueryExecutor
from zrtlib.selector import RandomSelector
from zrtlib.document import TermDocument, HiddenDocument

def func(incoming, outgoing, opts):
    log = logger.getlogger()

    with QueryExecutor() as engine:
        while True:
            (job, *payload) = incoming.get()

            if job == 'document':
                (document, ) = payload
                log.info('{0} {1}'.format(job, document))

                if QueryDoc.isquery(document):
                    info = QueryDoc.components(document)
                    value = (info.topic, HiddenDocument(document))
                else:
                    value = (None, TermDocument(document))

                outgoing.put(value)
            elif job == 'query':
                (topic, query) = payload
                log.info('{0} {1}'.format(job, topic))

                with NamedTemporaryFile(mode='w') as tmp:
                    query = QueryBuilder(opts.model, query)
                    print(query, file=tmp, flush=True)
                    result = engine.query(tmp.name, opts.index, opts.count)
                    result.check_returncode()

                values = []
                qrels = opts.qrels.joinpath(topic)
                for i in engine.evaluate(qrels, opts.count):
                    values.append(i[opts.metric])

                if values:
                    result = np.mean(values)
                else:
                    log.error('{0}: No values obtained'.format(topic))
                    result = np.nan

                outgoing.put((topic, result))
            elif job == 'quit':
                break

arguments = ArgumentParser()
arguments.add_argument('--model')
arguments.add_argument('--index')
arguments.add_argument('--metric')
arguments.add_argument('--selector')
arguments.add_argument('--guesses', type=int, default=np.inf)
arguments.add_argument('--count', type=int, default=1000)
arguments.add_argument('--qrels', type=Path)
arguments.add_argument('--input', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--compress-output', action='store_true')
args = arguments.parse_args()

log = logger.getlogger()

incoming = mp.Queue()
outgoing = mp.Queue()

with mp.Pool(initializer=func, initargs=(outgoing, incoming, args)):
    #
    #
    #
    results = {}
    queries = {}
    terms = RandomSelector()

    jobs = 0
    for i in zutils.walk(args.input):
        outgoing.put(('document', i))
        jobs += 1

    for _ in range(jobs):
        (topic, doc) = incoming.get()
        if topic is None:
            terms.add(doc)
        else:
            queries[topic] = doc
            results[topic] = float(0)

    #
    #
    #
    with args.output.open('w') as fp:
        fieldnames = [ 'term' ] + list(queries.keys())
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()

        predicate = lambda x: x < args.guesses
        for i in itertools.takewhile(predicate, itertools.count()):
            prior = results if i > 0 else None
            guess = next(terms.pick(prior))
            log.info(guess)

            changed = 0
            results['term'] = guess

            for (topic, query) in queries.items():
                if query.flip(guess) > 0:
                    outgoing.put(('query', topic, query))
                    changed += 1

            for _ in range(changed):
                (topic, value) = incoming.get()
                if not np.isnan(value):
                    results[topic] = value

            if not args.compress_output or args.compress_output and changed:
                writer.writerow(results)

            if not any(queries.values()):
                break

    for _ in range(mp.cpu_count()):
        outgoing.put('quit')
