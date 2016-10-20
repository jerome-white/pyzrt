import itertools
import operator as op

def pmap(f, iterable, start=0, stop=None):
    for (i, j) in enumerate(iterable):
        yield j if i < start or stop is not None and i >= stop else f(j)

def minval(iterable, item=0):
    return min(map(len, map(op.itemgetter(item), iterable)))


def count(start=0, stop=None, inclusive=True):
    rel = op.gt if inclusive else op.ge

    for i in itertools.count(start):
        if stop and rel(i, stop):
            break
        yield i
