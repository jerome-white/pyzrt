import random
from itertools import islice

from zrtlib.suffix import Suffix

def randstr(length, constraint=1):
    assert(0 <= constraint <= 1)
    
    a = 97
    z = round(a + 25 * constraint)
    alphabet = [ chr(x) for x in range(a, z) ]
    length = min(length, len(alphabet))

    string = random.sample(alphabet, length)

    return ''.join(string)

s = Suffix()

for i in range(4, 18):
    for _ in range(1000):
        key = randstr(i, 0.15)
        value = random.randrange(10)
        s.add(key, value)

s.dump()
# for i in s.ngrams(5):
#     print(i)
