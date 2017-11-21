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
    def __init__(self):
        self.qtype = 'queries'
        self.dtype = 'documents'

    def	__iter__(self):
        self._prime()
        return self

    def __next__(self):
        raise NotImplementedError()

    def gettype(self):
        return self.qtype if self.isquery() else self.dtype

    def isquery(self):
        raise NotImplementedError()

class Audio(_Parser):
    def __init__(self, document):
        super().__init__()

        self.document = document
        self.fp = None
        self.reader = None

    def _prime(self):
        self.fp = self.document.open()
        self.reader = csv.reader(self.fp, delimiter=' ')

    def __next__(self):
        try:
            (term, *duration) = next(self.reader)
        except StopIteration:
            self.fp.close()
            raise StopIteration()

        (start, stop) = map(int, duration)
        seconds = (stop - start) / 100

        return (term, seconds)

    def isquery(self):
        return str(self.document.stem).startswith('Q')

class Simulated(_Parser):
    def __init__(self, document):
        super().__init__()

        self.document = pz.TermCollection(document)
        self.itr = None

    def _prime(self):
        self.itr = iter(self.document)

    def __next__(self):
        term = next(self.itr)

        return (str(term), len(term))

    def isquery(self):
        return pz.TrecDocument.isquery(self.document.collection)

def func(incoming, outgoing, creator):
    parser = Parser(creator)

    while True:
        document = incoming.get()
        pz.util.get_logger().info(document.stem)

        terms = set()
        counts = cl.Counter()
        p = parser(document)

        for (term, duration) in p:
            terms.add(term)
            counts[duration] += 1

        result = Result(terms, counts, p.gettype())

        outgoing.put(result)

arguments = ArgumentParser()
arguments.add_argument('--terms', type=Path)
arguments.add_argument('--plot', type=Path)
arguments.add_argument('--save', type=Path)
arguments.add_argument('--creator')
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
arguments.add_argument('--x-min', type=float, default=0)
arguments.add_argument('--normalize', action='store_true')
args = arguments.parse_args()

assert(args.save or args.plot)

log = pz.util.get_logger(True)

names = ('corpus', 'documents', 'queries')
tallies = dict(zip(names, map(lambda x: x(), [ cl.Counter ] * 3)))
terms = set()

incoming = mp.Queue()
outgoing = mp.Queue()

with Pool(args.workers, func, (outgoing, incoming, args.creator)) as pool:
    jobs = pz.util.JobQueue(incoming, outgoing, args.terms.iterdir())

    for result in jobs:
        terms.update(result.terms)
        for i in ('corpus', result.doctype):
            tallies[i].update(result.counts)

log.debug('{0}'.format(len(terms)))

df = pd.DataFrame(tallies, columns=tallies.keys()).sort_index()
if args.normalize:
    df /= len(terms)

if args.save:
    df.to_csv(args.save, index_label='duration')

if args.plot:
    kwargs = {
        'aren': { 'xlim': (0, None) }
        None: {}
    }[args.creator]

    df.plot.line(grid=True, xlim=(args.x_min, None))
    plt.savefig(str(args.plot), bbox_inches='tight')
