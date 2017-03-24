import sys
import itertools
import operator as op
from pathlib import Path
from functools import singledispatch

#
# Read Indri stat output
#
def get_stats(directory, metric, summary):
    for i in directory.iterdir():
        with i.open() as fp:
            for line in fp:
                (metric_, run, value) = line.strip().split()
                aggregate = run == 'all'
                if not (summary ^ aggregate) and metric == metric_:
                    yield (i.stem, float(value))

def read_trec(fp, summary=False):
    previous = None
    results = {}

    for line in fp:
        (metric, run, value) = line.strip().split()
        if not summary and not run.isdigit():
            continue

        if previous is not None and previous != run:
            yield results
            results = {} # probably not necessary, but safe

        try:
            results[metric] = float(value)
        except ValueError:
            results[metric] = value

        previous = run

    if results and previous.isdigit():
        yield results

#
# Return on the metric value from Indri stat output
#
def summary_stats(directory, metric, summary):
    return [ x for (_, x) in get_stats(directory, metric, summary) ]

def cut(word, pos=1):
    return (word[0:pos], word[pos:])

def substrings(word, length=None):
    if length is None:
        length = len(word) - 1

    for i in range(len(word) - length + 1):
        yield word[i:i+length]

def pmap(f, iterable, start=0, stop=None):
    for (i, j) in enumerate(iterable):
        yield j if i < start or stop is not None and i >= stop else f(j)

def minval(iterable, item=0):
    return min(map(len, map(op.itemgetter(item), iterable)))

def minmax(iterable):
    (x, y) = (None, None)

    for i in iterable:
        if x is None or i < x:
            x = i
        if y is None or i > y:
            y = i

    return (x, y)

def count(start=0, stop=None, inclusive=True):
    rel = op.gt if inclusive else op.ge

    for i in itertools.count(start):
        if stop is not None and rel(i, stop):
            break
        yield i

@singledispatch
def walk(path):
    for p in path.iterdir():
        if p.is_dir():
            yield from walk(p)
        else:
            yield p

@walk.register(str)
def _(path):
    yield from walk(Path(path))

@walk.register(type(None))
def _(path):
    yield from map(lambda x: Path(x.strip()), sys.stdin)
