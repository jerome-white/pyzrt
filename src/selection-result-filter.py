import csv
import operator as op
import collections
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

from zrtlib import logger
from zrtlib.indri import QueryDoc

Entry = collections.namedtuple('Entry', 'guess, data')

def func(args):
    (path, opts) = args

    best = None    
    guesses = []
    
    with path.open() as fp:
        reader = csv.DictReader(fp)
        for line in reader:
            guess = int(line['guess'])
            guesses.append(guess)

            metric = float(line[opts.metric])
            if best is None or metric > best.data:
                best = Entry(guess, metric)

    x = max(guesses)
    (strategy, topic) = path.parts[-2:]
    
    print(strategy, topic, x, *best, sep='\t')

    return (strategy, Entry(x, topic))
        
arguments = ArgumentParser()
arguments.add_argument('--metric')
arguments.add_argument('--top-level', type=Path)
arguments.add_argument('--threshold', type=float, default=1.0)
args = arguments.parse_args()

with Pool() as pool:
    path = Path('**', QueryDoc.prefix + '*')
    iterable = map(lambda x: (x, args), args.top_level.glob(str(path)))
    guesses = collections.defaultdict(list)
    for (i, j) in pool.imap_unordered(func, iterable):
        guesses[i].append(j)

paths = []
for (key, values) in guesses.items():
    keep = []
    n = max(map(op.attrgetter('guess'), values))
    
    for i in values:
        if 1 - (n - i.guess) / n >= args.threshold:
            keep.append(i.data)

    for i in keep:
        paths.append(args.top_level.joinpath(key, i))
include = ' --include '
# print('--top-level', args.top_level,
#       '--metric', args.metric,
#       include, include.join(map(str, paths)))
