import random
from itertools import islice

from zrtlib.suffix import Suffix

def randstr(length, constraint=1):
    assert(0 <= constraint <= 1)
    
    a = 97
    z = min(a + 25, a + length)
    alphabet = [ chr(x) for x in range(a, z) ]
    random.shuffle(alphabet)

    return ''.join(alphabet)

s = Suffix()

for i in range(4, 6):
    for _ in range(10 ** 2):
        key = randstr(i)
        value = random.randrange(10)
        s.add(key, value)

s.dump()
# for i in s.ngrams(5):
#     print(i)
