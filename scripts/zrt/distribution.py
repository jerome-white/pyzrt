import collections as cl
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser

import pandas as pd
import matplotlib.pyplot as plt

import pyzrt as pz

_Stats = cl.namedtuple('_Stats', [
    'terms',     # terms per region
    'regions',   # regions per document
    'durations', # term length
])

class Stats(_Stats):
    def __new__(cls):
        args = map(lambda _: cl.Counter(), range(len(Stats._fields)))
        return super(Stats, cls).__new__(cls, *args)

    def __init__(self):
        self.unique = 0 # unique terms

    def extend(self, other):
        self.unique += other.unique

        for i in self._fields:
            (s, o) = [ getattr(x, i) for x in (self, other) ]
            s.update(o)

def Collection(corpus_type):
    return {
        'aren': pz.TermCollection.fromaren,
        'simulator': pz.TermCollection,
    }[corpus_type]

def func(incoming, outgoing, creator):
    log = pz.util.get_logger()

    stats = Stats()
    collection = Collection(creator)

    while True:
        document = incoming.get()
        if document is None:
            outgoing.put(stats)
            break
        log.info(document.stem)

        tc = collection(document)
        docstats = Stats()

        n = 0
        names = set()
        for region in tc.regions():
            docstats.terms[len(region)] += 1
            for term in region:
                names.add(str(term))
                docstats.durations[len(term)] += 1
            n += 1
        docstats.regions[n] += 1
        docstats.unique = len(names)

        stats.extend(docstats)

arguments = ArgumentParser()
arguments.add_argument('--terms', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--creator')
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
args = arguments.parse_args()

incoming = mp.Queue()
outgoing = mp.Queue()

with mp.Pool(args.workers, func, (outgoing, incoming, args.creator)):
    for i in args.terms.iterdir():
        outgoing.put(i)

    stats = Stats()
    for _ in range(args.workers):
        outgoing.put(None)
        stats.extend(incoming.get())

log = pz.util.get_logger(True)
log.info('BEGIN')

for i in Stats._fields:
    df = pd.Series(getattr(stats, i), name='count')
    dat = args.save.joinpath(i).with_suffix('.csv')
    df.to_csv(dat, header=True, index_label=i)

log.info('END')
