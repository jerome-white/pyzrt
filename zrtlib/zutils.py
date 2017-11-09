import sys
import csv
import itertools
import operator as op
import collections
from pathlib import Path
from functools import singledispatch

TrecMeasurement = collections.namedtuple('Measurement', 'run, results')

def stream(items, move=next, stop=None, compare=op.eq):
    '''Iterate through a sequence that doesn't strictly conform to
    Python's iterable semantics.

    '''

    while True:
        i = move(items)
        if compare(i, stop):
            break
        yield i

def read_baseline(baseline, metric, single_topics=True):
    '''Read the file created by baseline.py
    baseline (Path): path to baseline file
    metric (TrecMetric): metric of choice
    single_topics (Bool): whether to ensure topics are listed once

    '''
    seen = set()

    with baseline.open() as fp:
        reader = csv.DictReader(fp)
        for line in reader:
            topic = line['topic']
            if single_topics:
                assert(topic not in seen)
                seen.add(topic)
            yield (topic, float(line[repr(metric)]))

@singledispatch
def read_trec(fp, summary=False):
    previous = None
    summarised = False
    results = {}

    for line in fp:
        (metric, run, value) = line.strip().split()
        try:
            run = int(run)
            assert(run >= 0)
        except ValueError:
            run = -1

        if previous is not None and previous != run:
            assert(not summarised)

            yield TrecMeasurement(previous, results)
            results = {} # probably not necessary, but safe

            if run < 0:
                summarised = True

        try:
            results[metric] = float(value)
        except ValueError:
            results[metric] = value

        previous = run

    if results and (summary or run >= 0):
        yield TrecMeasurement(run, results)

@read_trec.register(Path)
def _(fp, summary=False):
    with fp.open() as ptr:
        yield from read_trec(ptr, summary)

@read_trec.register(str)
def _(fp, summary=False):
    yield from read_trec(Path(fp), summary)

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
    if path.is_dir():
        for i in path.iterdir():
            yield from walk(i)
    else:
        yield path

@walk.register(str)
def _(path):
    yield from walk(Path(path))

@walk.register(type(None))
def _(path):
    for i in sys.stdin:
        yield from walk(Path(i.strip()))
