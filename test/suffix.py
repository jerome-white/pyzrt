import sys
import random
from pathlib import Path
from argparse import ArgumentParser
from itertools import islice
from collections import Counter

from zrtlib.suffix import SuffixTree
from zrtlib.tokenizer import TokenSet, unstream

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
arguments.add_argument('--output', type=Path)
args = arguments.parse_args()

c = Counter()

if args.existing:
    s = SuffixTree.builder(args.existing, unstream, TokenSet)
else:
    s = SuffixTree(set)
    for i in range(4, 6):
        for _ in range(10 ** 2):
            key = randstr(i)
            value = randstr(1).upper() + str(random.randrange(10))
            s.add(key, value, 4)
            c[key] += 1

# for i in sorted(c):
#     print(i, c[i])

# print('.' * ROWS_)
# for (i, j) in c.items():
#     print(i, j, list(s.get(i)))

# for i in range(3, 7):
#     print(i, '.' * ROWS_)
#     for j in s.ngrams(i):
#         print(fmtkey(j), list(s.get(j)))

if args.output:
    with args.output.open('w') as fp:
        s.write(fp)
sys.exit()

# print('.' * ROWS_)
# for (i, j) in s.each():
#     print(fmtkey(i), j)

# print('.' * ROWS_)
# print(len(s))
# print(s.prune(1))
print(len(s))
s.compress()
print(len(s))

print('.' * ROWS_)
for (i, j) in s.each():
    print(fmtkey(i), j)

p1 = Path('psuedoterms')
p1.mkdir(exist_ok=True)
writer = PseudoTermWriter(s)
writer.write(p1)

p2 = Path('pt-files')
p2.mkdir(exist_ok=True)
writer.consolidate(p1, p2)
