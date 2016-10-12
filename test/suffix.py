import random
from itertools import islice
from collections import Counter

from zrtlib.suffix import SuffixTree

def randstr(length, constraint=1):
    assert(0 <= constraint <= 1)
    
    a = 97
    z = min(a + 25, a + length)
    alphabet = [ chr(x) for x in range(a, z) ]
    random.shuffle(alphabet)

    return ''.join(alphabet)

c = Counter()
s = SuffixTree()

for i in range(4, 6):
    for _ in range(10 ** 2):
        key = randstr(i)
        value = random.randrange(10)
        s.add(key, value, 4)
        c[key] += 1

# for i in sorted(c):
#     print(i, c[i])

s.dump()

# print('.' * 79)
# for (i, j) in s.each():
#     print(i, j)
# print('.' * 79)
# for (i, j) in c.items():
#     print(i, j, list(s.get(i)))

for i in range(3, 7):
    print('.' * 79)
    for j in s.ngrams(i):
        print(j, list(s.get(j)))
