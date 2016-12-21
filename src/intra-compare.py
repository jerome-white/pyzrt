import random
import operator as op
from pathlib import Path
from argparse import ArgumentParser
from collections import OrderedDict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from zrtlib import logger
from zrtlib import zutils
from zrtlib.color import HexColor

arguments = ArgumentParser()
arguments.add_argument('--metric', action='append')
arguments.add_argument('--all', action='store_true') # "all" or runs only?
arguments.add_argument('--zrt', type=Path)
arguments.add_argument('--baseline')
args = arguments.parse_args()

log = logger.getlogger()

metrics = {
    'map': 'MAP',
    'recip_rank': 'Reciprocal Rank',
}

naacl = pd.DataFrame.from_csv(args.baseline)

ngrams = []
models = []
for i in sorted(args.zrt.iterdir()):
    if i.stem not in ngrams:
        ngrams.append(i.stem)
    for j in sorted(i.iterdir(), reverse=True):
        if j.stem not in models:
            models.append(j.stem)

for metric in args.metric:
    color = HexColor()
    plots = []
    legend = []
    plt.clf()
    
    for (i, m) in enumerate(models):
        (x, y) = ([], [])
        for n in ngrams:
            log.info('{0} {1}'.format(m, n))
            path = Path(args.zrt, n, m)
            if not path.exists():
                log.warning('{0} does not exist'.format(path))
                continue
            stats = np.mean(zutils.summary_stats(path, metric, args.all))

            # XXX swap!
            x.append(stats)
            y.append(int(n))

        legend.append(m)
        marker = plt.matplotlib.markers.MarkerStyle.filled_markers[i]
        p = plt.scatter(x, y, marker=marker, c=next(color), edgecolors='face')
        plots.append(p)

    # for (j, k) in enumerate(('pure', 'medium', 'noisy'), i):

    plt.legend(plots, legend, loc='best')
    plt.grid()
    plt.axis('tight')
    plt.xlabel(metrics[metric])
    plt.ylabel('Model')

    fname = 'intra-{0}.png'.format(metric)
    plt.savefig(fname, bbox_inches='tight')
