import random
from pathlib import Path
from argparse import ArgumentParser
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt

from zrtlib import logger

class Colors:
    def __init__(self):
        self.used = set()
        self.fmt = '#' + '{:02X}' * 3

    def get(self):
        while True:
            vals = [ random.randrange(256) for _ in range(3) ]
            c = self.fmt.format(*vals)
            if c not in self.used:
                self.used.add(c)
                return c

def get_stats(directory, metric, summary):
    for i in directory.iterdir():
        with i.open() as fp:
            for line in fp:
                (metric_, run, value) = line.strip().split()
                aggregate = run == 'all'
                if not (summary ^ aggregate) and metric == metric_:
                    yield (i.stem, float(value))

def summary_stats(directory, metric, summary):
    return [ x for (_, x) in get_stats(directory, metric, summary) ]

# def pairs(directory, reverse=False):
#     for i in directory.iterdir():
#         for j in i.iterdir():
#             pair = [ i, j ]
#             if reverse:
#                 pair = reversed(pair)
#             yield tuple(pair)

arguments = ArgumentParser()
arguments.add_argument('--metric', action='append')
arguments.add_argument('--all', action='store_true') # "all" or runs only?
arguments.add_argument('--zrt', type=Path)
args = arguments.parse_args()

log = logger.getlogger()

metrics = {
    'map': 'MAP',
    'recip_rank': 'Reciprocal Rank',
    }

ngrams = []
models = []
for i in args.zrt.iterdir():
    if i.stem not in ngrams:
        ngrams.append(i.stem)
    for j in i.iterdir():
        if j.stem not in models:
            models.append(j.stem)

for metric in args.metric:
    colors = Colors()
    plots = []
    legend = []
    xticks = []
    
    for m in models:
        log.debug(m)
        
        (x, y) = ([], [])
        for n in ngrams:
            path = Path(args.zrt, n, m)
            xticks.append(m + '/' + n)
            if not path.exists():
                log.warning('{0} does not exist'.format(path))
                continue
            stats = np.mean(summary_stats(path, metric, args.all))
            
            x.append(stats)
            y.append(ngrams.index(n) + models.index(m))
        
        legend.append(m)
        p = plt.scatter(x, y, marker='o', c=colors.get(), edgecolors='face')
        plots.append(p)

    plt.legend(plots, legend, loc='best')
    plt.grid()
    plt.yticks(range(len(xticks)), xticks)
    plt.axis('tight')
    plt.xlabel(metrics[metric])
    plt.ylabel('model / n-grams')

    fname = 'intra-{0}.png'.format(metric)
    plt.savefig(fname, bbox_inches='tight')
