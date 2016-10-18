import pickle
import random
from pathlib import Path
from argparse import ArgumentParser
from itertools import islice
from collections import Counter

from zrtlib.suffix import SuffixTree
# from zrtlib.suffix import DebugSuffixTree as SuffixTree

ROWS_ = 70

def randstr(length, constraint=1):
    assert(0 <= constraint <= 1)
    
    a = 97
    z = min(a + 25, a + length)
    alphabet = [ chr(x) for x in range(a, z) ]
    random.shuffle(alphabet)

    return ''.join(alphabet)

def fmtkey(key):
    return "'" + key + "'"

arguments = ArgumentParser()
arguments.add_argument('--existing', type=Path)
args = arguments.parse_args()

c = Counter()
if args.existing:
    with args.existing.open('rb') as fp:
        s = pickle.load(fp)
else:
    s = SuffixTree()

    for i in range(4, 6):
        for _ in range(10 ** 2):
            key = randstr(i)
            value = random.randrange(10)
            s.add(key, value, 4)
            c[key] += 1

# for i in sorted(c):
#     print(i, c[i])

# s.dump()

print('.' * ROWS_)
for (i, j) in s.each():
    print(fmtkey(i), j)

# print('.' * ROWS_)
# for (i, j) in c.items():
#     print(i, j, list(s.get(i)))

for i in range(3, 7):
    print(i, '.' * ROWS_)
    for j in s.ngrams(i):
        print(fmtkey(j), list(s.get(j)))
