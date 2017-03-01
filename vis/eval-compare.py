import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from zrtlib import logger
from zrtlib import zutils
from zrtlib.indri import QueryDoc

def func(keys, incoming, outgoing):
    while True:
        (ngram, model, metric, aggregate) = incoming.get()

        for (topic, value) in zutils.get_stats(model, metric, aggregate):
            qid = QueryDoc.components(Path(topic))
            entry = [ int(ngram.stem), model.stem, qid.topic, value ]
            log.info(' '.join(map(str, entry[:-1])))

            outgoing.put(dict(zip(keys, entry)))

        outgoing.put(None)

def aquire(args):
    keys = [ 'n-grams', 'model', 'topic', metric ]
    incoming = mp.Queue()
    outgoing = mp.Queue()

    with mp.Pool(initializer=func, initargs=(keys, outgoing, incoming)):
        jobs = 0

        for ngram in args.zrt.iterdir():
            n = int(ngram.stem)
            if args.min_ngrams <= n <= args.max_ngrams:
                for model in ngram.iterdir():
                    outgoing.put((ngram, model, args.metric, args.all))
                    jobs += 1

        while jobs > 0:
            stats = incoming.get()
            if stats is None:
                jobs -= 1
            else:
                yield stats

arguments = ArgumentParser()
arguments.add_argument('--metric')
arguments.add_argument('--kind')
arguments.add_argument('--all', action='store_true') # "all" or runs only?
arguments.add_argument('--zrt', type=Path)
arguments.add_argument('--baseline', type=Path)
arguments.add_argument('--min-ngrams', type=int, default=0)
arguments.add_argument('--max-ngrams', type=float, default=np.inf)
args = arguments.parse_args()

log = logger.getlogger()

#
# Get the plotter options together first so that if they're wrong we
# haven't wasted any time mucking with data.
#
metric = {
    'map': 'Mean Average Precision',
    'recip_rank': 'Mean Reciprocal Rank',
}[args.metric]

(plotter, kwargs) = {
    'bar': (sns.barplot, { 'errwidth': 0.1 }),
    'point': (sns.pointplot, { 'ci': None }),
}[args.kind]

#
# Aquire the data
#
df = pd.DataFrame(aquire(args))
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

fname = 'evals-{1}-{0}.png'.format(args.kind, args.metric)
ax.figure.savefig(fname, bbox_inches='tight')
