import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile
from collections import Counter

import pandas as pd
import matplotlib.pyplot as plt

import pyzrt as pz

class Stats:
    def __init__(self):
        self.unique = 0 # unique terms

        self.terms = Counter()     # terms per region
        self.regions = Counter()   # regions per document
        self.durations = Counter() # term length
        self.fields = ['terms', 'regions', 'durations']

    def extend(self, other):
        self.unique += other.unique

        for i in self.fields:
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
arguments.add_argument('--version')
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

kwargs = {
    'dir': str(args.output),
    'mode': 'w',
    'delete': False,
    'suffix': '.csv',
}
version = '{0}-{1}'.format(args.creator[:2], args.version)

for field in stats.fields:
    with NamedTemporaryFile(**kwargs) as fp:
        pd.DataFrame({
            field: getattr(stats, field),
            'version': version,
        }).to_csv(fp, header=True, index_label='count')

log.info('END')
