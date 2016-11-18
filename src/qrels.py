import csv
import gzip
import tarfile
import itertools
from pathlib import Path
from argparse import ArgumentParser
from collections import defaultdict

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

arguments = ArgumentParser()
arguments.add_argument('--qrels', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--count', type=int, default=1)
arguments.add_argument('--include', action='append')
args = arguments.parse_args()

rels = defaultdict(list)

with tarfile.open(str(args.qrels), 'r:gz') as tar:
    for gz in tar.getmembers():
        with tar.extractfile(gz) as fp:
            lines = gzip.decompress(fp.read()).decode('utf-8').split('\n')
            for i in filter(None, lines):
                e = Entry(*i.split())
                if args.include and not any(map(e.istype, args.include)):
                    continue
                rels[e.topic].append(e)

for (topic, relevance) in rels.items():
    print(topic)

    path = args.output.joinpath(topic)
    with path.open('w') as fp:
        writer = csv.writer(fp, delimiter=' ')
        for entry in relevance:
            writer.writerows(entry.repeat(args.count))
