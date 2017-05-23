import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser

import numpy as np
import pandas as pd
import seaborn as sns
# import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from zrtlib import logger
from zrtlib import zutils
from zrtlib.indri import QueryDoc, TrecMetric
from zrtlib.jobqueue import SentinalJobQueue

def func(incoming, outgoing):
    while True:
        (ngram, model, metric, norms, non_zero) = incoming.get()

        for i in model.iterdir():
            qid = QueryDoc.components(i)

            n = 1
            if norms is not None:
                n = norms[qid.topic]
                if n == 0:
                    log.warning('Zero baseline {0}'.format(qid.topic))
                    if non_zero:
                        continue
                    n = 1

            with i.open() as fp:
                for (_, values) in zutils.read_trec(fp):
                    val = values[repr(metric)] / n
                    entry = (ngram, model.stem, qid.topic, val)
                    log.info(' '.join(map(str, entry[:-1])))
                    outgoing.put(entry)

        outgoing.put(None)

def mkjobs(args):
    if args.baseline is not None:
        norms = dict(zutils.read_baseline(args.baseline, args.metric))
    else:
        norms = None

    for ngram in args.zrt.iterdir():
        n = int(ngram.stem)
        if args.min_ngrams <= n <= args.max_ngrams:
            for model in ngram.iterdir():
                yield (n, model, args.metric, norms, args.non_zero)

def aquire(args, metric):
    keys = [ 'n-grams', 'model', 'topic', metric ]
    incoming = mp.Queue()
    outgoing = mp.Queue()

    initargs = (outgoing, incoming)
    with mp.Pool(initializer=func, initargs=initargs):
        for i in SentinalJobQueue(incoming, outgoing, mkjobs(args)):
            if i is not None:
                yield dict(zip(keys, i))

arguments = ArgumentParser()
arguments.add_argument('--metric', type=TrecMetric)
arguments.add_argument('--kind')
arguments.add_argument('--zrt', type=Path)
arguments.add_argument('--baseline', type=Path)
arguments.add_argument('--min-ngrams', type=int, default=0)
arguments.add_argument('--max-ngrams', type=float, default=np.inf)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--non-zero', action='store_true')
args = arguments.parse_args()

log = logger.getlogger()

#
# Get the plotter options together first so that if they're wrong we
# haven't wasted any time mucking with data.
#
metric = {
    'map': 'Mean Average Precision',
    'recip_rank': 'Mean Reciprocal Rank',
}[repr(args.metric)]
if args.baseline:
    metric = 'Relative ' + metric

(plotter, kwargs) = {
    'bar': (sns.barplot, { 'errwidth': 0.1 }),
    'point': (sns.pointplot, { 'ci': None }),
}[args.kind]

#
# Aquire the data
#
df = pd.DataFrame(aquire(args, metric))
# http://stackoverflow.com/a/42014251 ???

hues = df.model.unique()

#
# Plot
#
# plt.figure(figsize=(24, 6))
sns.set_context('paper')
sns.set(font_scale=1.7)
ax = plotter(x='n-grams',
             y=metric,
             hue='model',
             hue_order=sorted(hues),
             data=df,
             **kwargs)
ax.legend(ncol=round(len(hues) / 2), loc='upper center')
ax.set(ylim=(0, None),
       ylabel=metric)
if args.baseline:
    ax.yaxis.set_major_formatter(FuncFormatter('{0:.0%}'.format))

ax.figure.savefig(str(args.output), bbox_inches='tight')
