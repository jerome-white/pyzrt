import csv
import collections as cl
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser

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

def Collection(corpus_type, document):
    return {
        'aren': pz.TermCollection.fromaren,
        'simulator': pz.TermCollection,
    }[corpus_type](document)

def func(args):
    (document, creator) = args

    log = pz.util.get_logger()
    log.info(document.stem)

    n = 0
    names = set()
    stats = Stats()
    collection = Collection(creator, document)

    for region in collection.regions():
        stats.terms.append(len(region))
        for term in region:
            names.add(str(term))
            stats.durations.append(len(term))
        n += 1

    stats.regions.append(n)
    stats.unique = len(names)

    return stats

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

with mp.Pool(args.workers) as pool:
    stats = Stats()
    iterable = map(lambda x: (x, args.creator), args.terms.iterdir())
    for i in pool.imap_unordered(func, iterable):
        stats += i

log = pz.util.get_logger(True)
for i in ('terms', 'regions', 'durations'):
    df = pd.Series(getattr(stats, i), name=i)

    if args.save:
        dat = args.save.joinpath(i).with_suffix('.csv')
        log.info(dat)

        df.to_csv(dat, header=True, index_label='count')

    if args.plot:
        img = args.plot.joinpath(i).with_suffix('.png')
        log.info(img)

        df = df.value_counts().sort_index()

        if args.normalize:
            df /= df.sum()

        kwargs = {
            'aren': { 'xlim': (0, None) },
            None: {}
        }[args.creator]

        df.plot.line(grid=True, xlim=(args.x_min, None))

        plt.savefig(str(img), bbox_inches='tight')
        plt.clf()
