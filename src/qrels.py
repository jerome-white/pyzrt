import csv
import gzip
import tarfile
import itertools
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from collections import defaultdict

from zrtlib import logger

class Entry:
    def __init__(self, topic, iteration, document, relevancy):
        self.topic = topic
        self.iteration = iteration
        self.document = document
        self.relevancy = relevancy

    def istype(self, doctype):
        return self.document[:len(doctype)] == doctype

    def repeat(self, count):
        e = [ self.iteration, self.document, self.relevancy ]
        for (i, j) in enumerate(itertools.repeat(e, count)):
            yield [ i ] + j

def extract(fname, focus=None):
    with tarfile.open(str(fname), 'r:gz') as tar:
        for gz in tar.getmembers():
            with tar.extractfile(gz) as fp:
                lines = gzip.decompress(fp.read()).decode('utf-8').split('\n')
                for i in filter(None, lines):
                    entry = Entry(*i.split())
                    if focus and not any(map(entry.istype, focus)):
                        continue
                    yield entry

def write(output, jobs):
    log = logger.getlogger()

    while True:
        (topic, relevance) = jobs.get()
        log.info(topic)

        path = output.joinpath(topic)
        with path.open('w') as fp:
            writer = csv.writer(fp, delimiter=' ')
            for entry in relevance:
                writer.writerows(entry.repeat(args.count))

        jobs.task_done()

arguments = ArgumentParser()
arguments.add_argument('--qrels', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--include', action='append')
arguments.add_argument('--count', type=int, default=1)
args = arguments.parse_args()

jobs = mp.JoinableQueue()
with mp.Pool(initializer=write, initargs=(args.output, jobs)):
    rels = defaultdict(list)
    for entry in extract(args.qrels, args.include):
        rels[entry.topic].append(entry)

    for i in rels.items():
        jobs.put(i)
    jobs.join()
