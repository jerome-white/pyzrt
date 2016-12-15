import random
import operator as op
from pathlib import Path
from argparse import ArgumentParser
from collections import OrderedDict

import numpy as np
import matplotlib.pyplot as plt

from zrtlib import logger

class Colors:
    def __init__(self, buff=0.3):
        self.rgb = 256
        self.buff = buff
        self.used = OrderedDict([ (x, []) for x in [ 'r', 'g', 'b' ]])

    def ball(self, center):
        plus_minus = self.rgb * self.buff
        rng = [ round(f(center, plus_minus)) for f in (op.add, op.sub) ]
        yield from range(*rng)

    def get(self):
        i = 0
        keys = list(self.used.keys())

        while i < len(keys):
            k = keys[i]
            v = random.randrange(self.rgb)

            exists = False
            for j in self.ball(v):
                if j in self.used[k]:
                    exists = True
                    break

            if not exists:
                self.used[k].append(v)
                i += 1

        vals = [ self.used[x][-1] for x in keys ]

        return ('#' + '{:02X}' * 3).format(*vals)

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
for i in sorted(args.zrt.iterdir()):
    if i.stem not in ngrams:
        ngrams.append(i.stem)
    for j in sorted(i.iterdir(), reverse=True):
        if j.stem not in models:
            models.append(j.stem)

for metric in args.metric:
    colors = Colors()
    plots = []
    legend = []
    plt.clf()
    
    for m in models:
        (x, y) = ([], [])
        for n in ngrams:
            log.info('{0} {1}'.format(m, n))
            path = Path(args.zrt, n, m)
            if not path.exists():
                log.warning('{0} does not exist'.format(path))
                continue
            stats = np.mean(summary_stats(path, metric, args.all))
            
            x.append(stats)
            y.append(int(n))

        legend.append(m)
        p = plt.scatter(x, y, marker='o', c=colors.get(), edgecolors='face')
        plots.append(p)

    plt.legend(plots, legend, loc='best')
    plt.grid()
    plt.axis('tight')
    plt.xlabel(metrics[metric])
    plt.ylabel('model / n-grams')

    fname = 'intra-{0}.png'.format(metric)
    plt.savefig(fname, bbox_inches='tight')
