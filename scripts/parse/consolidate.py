#
# Consolidate a collection of formatted TREC files into a single CSV.
#

import sys
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser

import numpy as np
import pandas as pd

import pyzrt as pz

class ResultReader:
    def __init__(self, metrics):
        self.metrics = metrics

    def get(self, path, usecols):
        df = pd.read_csv(path, usecols=usecols)
        id_vars = df.columns.difference(self.metrics)

        return df.melt(id_vars=id_vars,
                       value_vars=self.metrics,
                       var_name='metric',
                       value_name='value')

def func(incoming, outgoing, args, metrics):
    log = pz.util.get_logger()

    reader = ResultReader(metrics)
    usecols = ['num_rel', 'query'] + metrics

    if args.baseline:
        base = reader.get(args.baseline, usecols)
        base['query'] = base['query'].apply(lambda x: 'Q{0:03d}'.format(x))
    else:
        base = None

    usecols.extend(['model', 'ngrams'])

    while True:
        result = incoming.get()
        log.info(result.stem)

        df = reader.get(result, usecols)
        assert(len(df) == len(metrics))

        if base is not None:
            df = df.merge(base,
                          on=['query', 'metric'],
                          suffixes=('', '_baseline'))
            df.drop(columns='num_rel_baseline', inplace=True)

        outgoing.put(df)

def aquire(args, metrics):
    incoming = mp.Queue()
    outgoing = mp.Queue()

    with mp.Pool(args.workers, func, (outgoing, incoming, args, metrics)):
        jobs = 0
        for i in args.data.iterdir():
            if i.stat().st_size:
                outgoing.put(i)
                jobs += 1

        for _ in range(jobs):
            yield incoming.get()

arguments = ArgumentParser()
arguments.add_argument('--data', type=Path)
arguments.add_argument('--baseline', type=Path)
arguments.add_argument('--metric', action='append')
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
args = arguments.parse_args()

metrics = [ repr(pz.TrecMetric(x)) for x in args.metric ]

pd.concat(aquire(args, metrics)).to_csv(sys.stdout, index=False)
