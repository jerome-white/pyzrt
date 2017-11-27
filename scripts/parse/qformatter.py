#
# Formats a raw query (data/query) into the DOC/DOCNO/TEXT format
# required for TREC (and ultimately) for the parser.
#

import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser

import pyzrt as pz

def func(queue, with_topic, output):
    log = pz.util.get_logger(True)

    while True:
        doc = queue.get()
        qdocs = pz.TrecDocument(doc)

        with doc.open() as fp:
            q = []
            topic = with_topic
            for j in fp:
                line = j.strip()
                if line:
                    q.append(line)
                else:
                    if topic:
                        qdocs.add(q)
                    q = []
                    topic = True

            if q and topic:
                qdocs.add(q)

        if qdocs:
            fname = 'WSJ_Q' + doc.stem
            log.info(fname)
            with output.joinpath(fname).open('w') as fp:
                for j in qdocs:
                    fp.write(j)

        queue.task_done()

    return args

arguments = ArgumentParser()
arguments.add_argument('--input', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--with-topic', action='store_true')
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
args = arguments.parse_args()

log = pz.util.get_logger(True)
log.info('>| begin')

queue = mp.JoinableQueue()
with mp.Pool(args.workers, func, (queue, args.with_topic, args.output)):
    for i in args.input.iterdir():
        if i.stem.isdigit():
            queue.put(i)
    queue.join()

log.info('<| complete')
