import collections as cl
from pathlib import Path
from functools import singledispatch

TrecMeasurement = cl.namedtuple('TrecMeasurement', 'run, results')

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
