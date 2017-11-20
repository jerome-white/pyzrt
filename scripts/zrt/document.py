import csv
import collections as cl
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

# import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

import pyzrt as pz

Result = cl.namedtuple('Result', 'terms, counts, doctype')

def Parser(corpus_type):
    return {
        'aren': Audio,
        'simulator': Simulated,
    }[corpus_type]

class _Parser:
    def	__iter__(self):
        self._prime()
        return self

    def __next__(self):
        raise NotImplementedError()

    def gettype(self):
        return self.qtype if self.isquery() else self.dtype

class Audio(_Parser):
    def __init__(self, document):
        self.document = document
        self.fp = None
        self.reader = None

    def _prime(self):
        self.fp = self.document.open()
        self.reader = csv.reader(self.fp, delimiter=' ')

    def __next__(self):
        try:
            (_, *duration) = next(self.reader)
        except StopIteration:
            self.fp.close()
            raise StopIteration()

        return list(map(round, map(lambda x: x / 100, map(int, duration))))

class Simulated(_Parser):
    def __init__(self, document):
        self.collection = pz.TermCollection(document)
        self.itr = None

    def _prime(self):
        self.itr = iter(self.collection)

    def __next__(self):
        term = next(self.itr)

        return (term.position, term.end())

def func(incoming, outgoing, creator):
    parser = Parser(creator)

    while True:
        document = incoming.get()
        pz.util.get_logger().info(document.stem)

        counts = cl.Counter()

        for (start, stop) in parser(document):
            for i in range(start, stop + 1):
                counts[i] += 1

        outgoing.put(counts)

arguments = ArgumentParser()
arguments.add_argument('--terms', type=Path)
arguments.add_argument('--plot', type=Path)
arguments.add_argument('--save', type=Path)
arguments.add_argument('--creator')
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
# arguments.add_argument('--normalize', action='store_true')
args = arguments.parse_args()

assert(args.save or args.plot)

log = pz.util.get_logger(True)

counts = cl.defaultdict(list)
incoming = mp.Queue()
outgoing = mp.Queue()

with Pool(args.workers, func, (outgoing, incoming, args.creator)) as pool:
    jobs = pz.util.JobQueue(incoming, outgoing, args.terms.iterdir())

    for result in jobs:
        for (pos, tally) in result.items():
            counts[pos].append(tally)

log.debug('{0}'.format(len(counts)))

df = pd.DataFrame.from_dict(counts, orient='index').transpose()
df = df.reindex(sorted(df.columns), axis='columns')

if args.save:
    df.to_csv(args.save, index_label='duration')

if args.plot:
    fig = plt.gcf()
    (width, height) = fig.get_size_inches()
    plt.rcParams["figure.figsize"] = (width ** 2, height)

    df.plot.box(grid=True, showfliers=False)
    plt.savefig(str(args.plot), bbox_inches='tight')
