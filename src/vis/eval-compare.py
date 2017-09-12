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
from zrtlib.jobqueue import JobQueue

def func(incoming, outgoing, args):
    log = logger.getlogger()

    metric = repr(args.metric)
    usecols=[ metric, 'model', 'query' ] # see query/models.py

    if args.baseline is None:
        norms = None
    else:
        norms = dict(zutils.read_baseline(args.baseline, args.metric))

    while True:
        (result, ngrams) = incoming.get()
        log.info('{0} {1} {2}'.format(metric, ngrams, result.stem))

        query = pd.read_csv(result, usecols=usecols)
        topic = QueryDoc.components(query).topic

        if norms and norms[topic] == 0:
            log.warning('Skipping {0}'.format(topic))
            df = None
        else:
            df.drop('query', axis=1, inplace=True)
            df = df.assign(ngrams=args.ngrams, topic=topic)
            if args.baseline:
                df[metric] /= norms[topic]

        outgoing.put(df)

def jobs(args):
    for ngram in args.zrt.iterdir():
        assert(ngram.is_dir())

        ngram = int(ngram.stem)
        if args.min_ngrams <= ngram <= args.max_ngrams:
            for result in ngram.iterdir():
                yield (result, ngram)

def aquire(args):
    incoming = mp.Queue()
    outgoing = mp.Queue()

    initargs = (outgoing, incoming, args)

    with mp.Pool(processes=args.workers, initializer=func, initargs=initargs):
        queue = JobQueue(incoming, outgoing, jobs(args))
        yield from filter(None, queue)

arguments = ArgumentParser()
arguments.add_argument('--kind')
arguments.add_argument('--common', action='store_true')
arguments.add_argument('--zrt', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--metric', type=TrecMetric)
arguments.add_argument('--baseline', type=Path)
arguments.add_argument('--min-ngrams', type=int, default=0)
arguments.add_argument('--max-ngrams', type=float, default=np.inf)
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
args = arguments.parse_args()

log = logger.getlogger(True)

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

(plotter, kwargs) = {
    'bar': (sns.barplot, { 'errwidth': 0.1 }),
    'point': (sns.pointplot, { 'ci': None }),
}[args.kind]

#
# Aquire the data
#
df = pd.concat(aquire(args))
df.to_csv('a.csv')

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

topics = df['topic'].unique()
log.info('Topics ({0}): {1}'.format(len(topics), ','.join(map(str, topics))))

#
# Plot
#
hues = df['model'].unique()

# plt.figure(figsize=(24, 6))
sns.set_context('paper')
sns.set(font_scale=1.7)
ax = plotter(x='ngrams',
             y=repr(args.metric),
             hue='model',
             hue_order=sorted(hues),
             data=df,
             **kwargs)
ax.legend(ncol=round(len(hues) / 2), loc='upper center')
ax.set(ylim=(0, None),
       ylabel=metric_label)
if args.baseline:
    ax.yaxis.set_major_formatter(FuncFormatter('{0:.0%}'.format))

ax.figure.savefig(str(args.output), bbox_inches='tight')
