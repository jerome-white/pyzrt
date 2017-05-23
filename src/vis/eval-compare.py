from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

import numpy as np
import pandas as pd
import seaborn as sns
# import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from zrtlib import logger
from zrtlib import zutils
from zrtlib.indri import QueryDoc, TrecMetric

class Argument:
    def __init__(self, path, metric, baseline=None):
        self.path = path
        self.metric = repr(metric)
        self.baseline = baseline

        self.ngrams = int(self.path.parts[-2])
        self.topic = QueryDoc.components(self.path).topic

    def __str__(self):
        return ' '.join(map(str, (self.metric, self.ngrams, self.topic)))

def func(args):
    log = logger.getlogger()
    log.info(args)

    df = pd.read_csv(args.path, usecols=[ args.metric, 'model' ])
    df = df.assign(ngrams=args.ngrams, topic=args.topic)

    if args.baseline:
        factor = args.baseline[args.topic]
        if factor == 0:
            return
        df[args.metric] /= factor

    return df

def jobs(args):
    if args.baseline is None:
        norms = None
    else:
        norms = dict(zutils.read_baseline(args.baseline, args.metric))
        for i in norms.items():
            log.debug('{0} {1}'.format(*i))

    for ngram in args.zrt.iterdir():
        n = int(ngram.stem)
        if args.min_ngrams <= n <= args.max_ngrams:
            for topic in ngram.iterdir():
                yield Argument(topic, args.metric, norms)

def aquire(args):
    with Pool() as pool:
        yield from pool.imap_unordered(func, jobs(args))

arguments = ArgumentParser()
arguments.add_argument('--metric', type=TrecMetric)
arguments.add_argument('--kind')
arguments.add_argument('--zrt', type=Path)
arguments.add_argument('--baseline', type=Path)
arguments.add_argument('--min-ngrams', type=int, default=0)
arguments.add_argument('--max-ngrams', type=float, default=np.inf)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--common', action='store_true')
arguments.add_argument('--non-zero', action='store_true')
args = arguments.parse_args()

log = logger.getlogger()

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
log.info('Topics {0}'.format(len(df['topic'].unique())))

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
