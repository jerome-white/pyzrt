import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import FuncFormatter

import pyzrt as pz

def func(incoming, outgoing, args):
    log = pz.util.get_logger()

    metrics = map(repr, (pz.TrecMetric, args.metric))
    usecols = ['num_rel', 'query'] + metrics

    if args.baseline:
        base = pd.read_csv(args.baseline, usecols=usecols)
    else:
        base = None

    while True:
        result = incoming.get()
        log.info(result.stem)

        df = pd.read_csv(result, usecols=usecols + ['model', 'ngrams']))
        assert(len(df) == 1)

        if base is not None:
            query = df.at[0, 'query']
            if query not in base or base[query] == 0:
                df = None
            else:
                for i in metrics:
                    df[i] /= base[i]

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
df = df[df['num_rel'] >= args.min_relevant]
if args.save_data:
    df.to_csv(args.save_data)

hues = df['model'].unique()
# sns.set_context('paper')
#sns.set(font_scale=1.7)
sns.set_style('whitegrid')
ax = sns.pointplot(x='ngrams',
                   y=repr(args.metric),
                   hue='model',
                   hue_order=sorted(hues),
                   ci=None,
                   data=df)
ax.legend(ncol=round(len(hues) / 2), loc='upper center')
ax.set(ylim=(0, None))
#       ylabel=metric_label)

ax.figure.savefig(str(args.output), bbox_inches='tight')
