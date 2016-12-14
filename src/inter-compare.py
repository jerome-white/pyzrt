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

baseline = summary_stats(args.baseline, args.metric, args.all)

#
# Gather the stats
#
results = defaultdict(dict)
for ngram in args.zrt.iterdir():
    for model in ngram.iterdir():
        stats = summary_stats(model, args.metric, args.all)
        results[model.stem][ngram.stem] = stats

#
# Plot
#
for model in results:
    labels = [ '' ]
    data = [ baseline ]
    
    for (ngram, stats) in results[model].items():
        labels.append(ngram)
        data.append(stats)
        
    plt.boxplot(data, labels=labels, showfliers=False)
    plt.ylim(ymin=0)
    plt.grid(which='both', axis='y')
    plt.title(model)
    plt.ylabel(metrics[args.metric])

    fname = args.plots.joinpath(model).with_suffix('.png')
    plt.savefig(str(fname))
