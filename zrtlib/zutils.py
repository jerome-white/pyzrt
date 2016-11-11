import itertools
import operator as op

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
        if stop and rel(i, stop):
            break
        yield i