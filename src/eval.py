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

arguments = ArgumentParser()
arguments.add_argument('--metric')
arguments.add_argument('--all', action='store_true') # all or runs only?
arguments.add_argument('--evals', action='append', type=Path)
args = arguments.parse_args()

results = {}
for i in args.evals:
    results[i.stem] = [ x for (_, x) in get_stats(i, args.metric, args.all) ]
print(results)
