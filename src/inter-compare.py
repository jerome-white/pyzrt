from pathlib import Path
from argparse import ArgumentParser
from collections import defaultdict

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
arguments.add_argument('--metric')
arguments.add_argument('--all', action='store_true') # "all" or runs only?
arguments.add_argument('--plots', type=Path)
arguments.add_argument('--zrt', type=Path)
arguments.add_argument('--baseline', type=Path)
args = arguments.parse_args()

metrics = {
    'map': 'MAP',
    'recip_rank': 'Reciprocal Rank',
    }

labels = [ 'std' ]
baseline = [ summary_stats(args.baseline, args.metric, args.all) ]

for ngram in args.zrt.iterdir():
    for model in ngram.iterdir():
        lbl = '{0}-{1}'.format(ngram, model.lower())
        stats = summary_stats(model, args.metric, args.all)
        
        labels.append(lbl)
        data.append(stats)
        
plt.boxplot(data, labels=labels, showfliers=False)

plt.ylim(ymin=0)
plt.grid(which='both', axis='y')
plt.title(model)
plt.ylabel(metrics[args.metric])

plt.savefig(args.metric + '.png')
