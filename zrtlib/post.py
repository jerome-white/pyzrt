import sys
import operator as op
from pathlib import Path
from collections import namedtuple, defaultdict

IndexedToken = namedtuple('IndexedToken', 'index, segment')

class Posting(defaultdict):
    def __init__(self, segmenter, to_string):
        super().__init__(list)

        for (i, segment) in enumerate(map(op.itemgetter(1), segmenter.each())):
            segment_string = to_string(segment)
            self[segment_string].append(IndexedToken(i, segment))

    def __int__(self):
        return sum(map(len, self.values()))

    def frequency(self, segment_string):
        return len(self[segment_string])

    def weight(self, segment_string):
        # max_freq = None
        # segment_freq = 0

        # for i in self.keys():
        #     freq = self.frequency(i)
        #     if max_freq is None or max_freq < freq:
        #         max_freq = freq
        #     if i == segment_string:
        #         segment_freq = freq

        # return segment_freq / max_freq

        return 1 / self.frequency(segment_string)

    def mass(self, segment_string):
        return self.frequency(segment_string) / int(self)

    def each(self, segment_string):
        yield from map(op.attrgetter('index'), self[segment_string])
