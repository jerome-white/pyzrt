import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from collections import Counter

import pandas as pd
import matplotlib.pyplot as plt

import pyzrt as pz

class Stats:
    def __init__(self):
        self.unique = 0 # unique terms
        self.terms = Counter() # terms per region
        self.regions = Counter() # regions per document
        self.durations = Counter() # term length

    def extend(self, other):
        self.unique += other.unique

        for i in ('terms', 'regions', 'durations'):
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
arguments.add_argument('--plot', type=Path)
arguments.add_argument('--save', type=Path)
arguments.add_argument('--creator')
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
arguments.add_argument('--x-min', type=float, default=0)
arguments.add_argument('--normalize', action='store_true')
args = arguments.parse_args()

assert(args.save or args.plot)

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
for i in ('terms', 'regions', 'durations'):
    df = pd.Series(getattr(stats, i), name='count')

    if args.save:
        dat = args.save.joinpath(i).with_suffix('.csv')
        log.info(dat)

        df.to_csv(dat, header=True, index_label=i)

    if args.plot:
        img = args.plot.joinpath(i).with_suffix('.png')
        log.info(img)

        if args.normalize:
            df /= df.sum()

        df.plot.line(grid=True, xlim=(args.x_min, None))

        plt.savefig(str(img), bbox_inches='tight')
        plt.clf()
log.info('END')
