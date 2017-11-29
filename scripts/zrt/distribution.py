import csv
import collections as cl
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

import pandas as pd
import matplotlib.pyplot as plt

import pyzrt as pz

class Stats:
    def __init__(self):
        self.unique = 0 # unique terms
        self.terms = [] # terms per region
        self.regions = [] # regions per document
        self.durations = [] # term length

    def __add__(self, other):
        result = type(self)()

        result.terms = self.terms + other.terms
        result.unique = self.unique + other.unique
        result.regions = self.regions + other.regions
        result.durations = self.durations + other.durations

        return result

def Collection(corpus_type):
    return {
        'aren': pz.TermCollection.fromaren,
        'simulator': pz.TermCollection,
    }[corpus_type]

def func(incoming, outgoing, creator):
    log = pz.util.get_logger()

    collection = Collection(creator)

    while True:
        document = incoming.get()
        log.info(document.stem)

        names = set()
        stats = Stats()
        tc = collection(document)

        n = 0
        for region in tc.regions():
            stats.terms.append(len(region))
            for term in region:
                names.add(str(term))
                stats.durations.append(len(term))
            n += 1

        stats.regions.append(n)
        stats.unique = len(names)

        outgoing.put(stats)

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

incoming = mp.Queue()
outgoing = mp.Queue()

with Pool(args.workers, func, (outgoing, incoming, args.creator)) as pool:
    jobs = pz.util.JobQueue(incoming, outgoing, args.terms.iterdir())
    # stats = sum(jobs)
    stats = Stats()
    for i in jobs:
        stats += i

for i in ('terms', 'regions', 'durations'):
    df = pd.Series(getattr(stats, i), name=i)

    if args.save:
        dat = args.save.joinpath(i).with_suffix('.csv')
        df.to_csv(dat, header=True, index_label='count')

    if args.plot:
        df = df.value_counts().sort_index()

        if args.normalize:
            df /= df.sum()

        kwargs = {
            'aren': { 'xlim': (0, None) },
            None: {}
        }[args.creator]

        df.plot.line(grid=True, xlim=(args.x_min, None))

        img = args.plot.joinpath(i).with_suffix('.png')
        plt.savefig(str(img), bbox_inches='tight')
        plt.clf()
