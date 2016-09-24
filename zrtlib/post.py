import sys
import operator as op
from pathlib import Path
from collections import namedtuple, defaultdict

IndexedToken = namedtuple('IndexedToken', 'index, token')

class Posting(defaultdict):
    def __init__(self, tokenizer, transcribe):
        super().__init__(list)

        for (i, token) in tokenizer.each():
            key = transcribe(token)
            value = self.mkentry(i, token)
            self[key].append(value)

    def __int__(self):
        return sum(map(len, self.values()))

    def frequency(self, key):
        return len(self[key])

    def weight(self, key):
        # max_freq = None
        # segment_freq = 0

        # for i in self.keys():
        #     freq = self.frequency(i)
        #     if max_freq is None or max_freq < freq:
        #         max_freq = freq
        #     if i == segment_string:
        #         segment_freq = freq

        # return segment_freq / max_freq

        return 1 / self.frequency(key)

    def mass(self, key):
        return self.frequency(key) / int(self)

    def mkentry(self, i, token):
        return i

    def each(self, key):
        yield from self[key]

    def invert(self):
        yield from [ (y, x) for (x, y) in self.items() ]

class ExtendedPosting(Posting):
    def mkentry(self, i, token):
        return IndexedToken(i, token)

    def each(self, key):
        yield from map(op.attrgetter('index'), self[key])
