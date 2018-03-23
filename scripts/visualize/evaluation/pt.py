import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

import pyzrt as pz

def func(incoming, outgoing, args):
    log = pz.util.get_logger()

    metrics = [ repr(pz.TrecMetric(x)) for x in args.metric ]
    usecols = ['num_rel', 'query']

    if args.baseline:
        base = pd.read_csv(args.baseline, usecols=usecols + metrics)
    else:
        base = None

    usecols.extend(['model', 'ngrams'])
    while True:
        result = incoming.get()
        log.info(result.stem)

        df = pd.read_csv(result, usecols=usecols + metrics)
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
# arguments.add_argument('--model')
arguments.add_argument('--data', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--metric', action='append')
arguments.add_argument('--baseline', type=Path)
arguments.add_argument('--save-data', type=Path)
arguments.add_argument('--min-relevant', type=int, default=0)
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
args = arguments.parse_args()

metric_label = {
    'map': 'MAP',
    'recip_rank': 'Mean Reciprocal Rank',
    'ndcg': 'NDCG',
}

df = pd.concat(aquire(args))
if args.save_data:
    df.to_csv(args.save_data, index=False)

df = (df[df['num_rel'] >= args.min_relevant]
      .melt(id_vars=['num_rel', 'query', 'model', 'ngrams'],
             value_vars=args.metrics, # assumes args are Trec friendly
             var_name='metric',
             value_name='result')
      .sort_values(by=['metric', 'ngrams', 'model'])
      .drop(['num_rel', 'query'], axis='columns'))

# sns.set_context('paper')
#sns.set(font_scale=1.7)
sns.set_style('whitegrid')

g = sns.PairGrid(crashes.sort_values("total", ascending=False),
                 x_vars=crashes.columns[:-3], y_vars=["abbrev"],
                 size=10, aspect=.25)

plt.savefig(str(args.output), bbox_inches='tight')
