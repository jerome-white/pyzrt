from pathlib import Path
from argparse import ArgumentParser
from collections import defaultdict

import matplotlib.pyplot as plt

from zrtlib import logger
from zrtlib import zutils

arguments = ArgumentParser()
arguments.add_argument('--metric', action='append')
arguments.add_argument('--all', action='store_true') # "all" or runs only?
arguments.add_argument('--zrt', type=Path)
arguments.add_argument('--baseline', type=Path)
args = arguments.parse_args()

log = logger.getlogger()

metrics = {
    'map': 'MAP',
    'recip_rank': 'Reciprocal Rank',
    }

for metric in args.metric:
    labels = [ '\nSTD' ]
    data = [ zutils.summary_stats(args.baseline, metric, args.all) ]
    
    for ngram in args.zrt.iterdir():
        for model in ngram.iterdir():
            lbl = '{0}\n{1}'.format(ngram.stem, model.stem.lower())
            stats = zutils.summary_stats(model, metric, args.all)
        
            log.info(lbl.replace('\n', ' '))
            
            labels.append(lbl)
            data.append(stats)

    width = len(labels) * 0.75
    plt.figure(figsize=(width, 12))
    plt.boxplot(data, labels=labels, showfliers=False)

    plt.ylim(ymin=0)
    plt.grid(which='both', axis='y')
    plt.ylabel(metrics[metric])

    fname = 'inter-{0}.png'.format(metric)
    plt.savefig(fname, bbox_inches='tight')
