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

def func(incoming, outgoing, args):
    log = pz.util.get_logger()

    metrics = [ repr(pz.TrecMetric(x)) for x in args.metric ]
    usecols = ['num_rel', 'query'] + metrics

    if args.baseline:
        base = pd.read_csv(args.baseline, usecols=usecols)
    else:
        base = None

    usecols.extend(['model', 'ngrams'])
    while True:
        result = incoming.get()
        log.info(result.stem)

        df = pd.read_csv(result, usecols=usecols)
        assert(len(df) == 1)

        if base is not None:
            query = []
            for i in df.at[0, 'query']:
                if i.isdigit():
                    query.append(i)
            query = int(''.join(query))

            spot = base[base['query'] == query][metrics]
            if spot.empty:
                df[metrics] = np.nan
            else:
                df[metrics] /= spot.reset_index(drop=True)

        outgoing.put(df)

def aquire(args):
    incoming = mp.Queue()
    outgoing = mp.Queue()

    with mp.Pool(args.workers, func, (outgoing, incoming, args)):
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

pd.concat(aquire(args)).to_csv(sys.stdout, index=False)
