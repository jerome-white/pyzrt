import functools as ft
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser

import numpy as np
import pandas as pd
import seaborn as sns
# import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

import pyzrt as pz

def func(incoming, outgoing, args):
    log = pz.util.get_logger()

    metric = repr(args.metric)
    usecols=[ metric, 'model', 'query' ] # see query/models.py

    if args.baseline is None:
        norms = None
    else:
        norms = dict(pz.util.read_baseline(args.baseline, args.metric))

    while True:
        (result, ngrams) = incoming.get()
        log.info('{0} {1} {2}'.format(metric, ngrams, result.stem))

        df = pd.read_csv(result, usecols=usecols)
        assert(len(df) == 1)
        query = Path(df.iat[0, df.columns.get_loc('query')])
        topic = pz.TrecDocument.components(query).topic

        if norms and norms[topic] == 0:
            log.warning('Skipping {0}'.format(topic))
            df = None
        else:
            df.drop('query', axis=1, inplace=True)
            df = df.assign(ngrams=ngrams, topic=topic)
            if args.baseline:
                df[metric] /= norms[topic]

        outgoing.put(df)

def jobs(args):
    for ngram in args.zrt.iterdir():
        assert(ngram.is_dir())

        n = int(ngram.stem)
        if args.min_ngrams <= n <= args.max_ngrams:
            for result in ngram.iterdir():
                yield (result, n)

def aquire(args):
    incoming = mp.Queue()
    outgoing = mp.Queue()

    with mp.Pool(args.workers, func, (outgoing, incoming, args)):
        queue = pz.util.JobQueue(incoming, outgoing, jobs(args))
        for i in queue:
            if i is not None:
                yield i

arguments = ArgumentParser()
arguments.add_argument('--kind', default='point')
arguments.add_argument('--y-max', type=float, default=None)
arguments.add_argument('--common', action='store_true')
arguments.add_argument('--zrt', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--metric', type=pz.TrecMetric)
arguments.add_argument('--baseline', type=Path)
arguments.add_argument('--min-ngrams', type=int, default=0)
arguments.add_argument('--max-ngrams', type=float, default=np.inf)
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
arguments.add_argument('--model', action='append')
arguments.add_argument('--save-data', type=Path)
args = arguments.parse_args()

log = pz.util.get_logger(True)

#
# Get the plotter options together first so that if they're wrong we
# haven't wasted any time mucking with data.
#
metric_label = {
    'map': 'Mean Average Precision',
    'recip_rank': 'Mean Reciprocal Rank',
}[repr(args.metric)]

if args.baseline:
    metric_label = 'Relative ' + metric_label

plot = {
    'bar': ft.partial(sns.barplot, errwidth=0.1),
    'point': ft.partial(sns.pointplot, ci=None),
    'strip': ft.partial(sns.stripplot),
}[args.kind]

#
# Aquire the data
#
df = pd.concat(aquire(args))

if args.model:
    df = df[df['model'].isin(args.model)]

if args.common:
    common = set()
    for (_, i) in df.groupby('ngrams', sort=False):
        topics = i['topic']
        if not common:
            common.update(topics)
        else:
            common = common.intersection(topics)
    log.debug(common)
    df = df[df['topic'].isin(common)]

assert(not df.empty)

topics = np.sort(df['topic'].unique())
log.info('Topics ({0}): {1}'.format(len(topics), ','.join(map(str, topics))))

#
# Plot
#
hues = df['model'].unique()

# plt.figure(figsize=(24, 6))
sns.set_context('paper')
#sns.set(font_scale=1.7)
sns.set_style("whitegrid")
ax = plot(x='ngrams',
          y=repr(args.metric),
          hue='model',
          hue_order=sorted(hues),
          data=df)
ax.legend(ncol=round(len(hues) / 2), loc='upper center')
ax.set(ylim=(0, args.y_max),
       ylabel=metric_label)
if args.baseline:
    ax.yaxis.set_major_formatter(FuncFormatter('{0:.0%}'.format))

ax.figure.savefig(str(args.output), bbox_inches='tight')

if args.save_data:
    df.to_csv(args.save_data)
