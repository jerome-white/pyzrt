import itertools
import collections
from functools import singledispatch

import numpy as np

@singledispatch
def average(values):
    return average(list(values))

@average.register(list)
def _(values):
    weights = np.linspace(1, 2, len(values))
    return np.average(values, weights=weights) if weights.size > 0 else 0

class FeedbackHandler(collections.deque):
    def __init__(self, maxlen=1):
        super().__init__(maxlen=maxlen)

    def __float__(self):
        raise NotImplementedError()

    def __int__(self):
        raise NotImplementedError()

    def __str__(self):
        return str(self[-1] if self else None)

class RecentWeighted(FeedbackHandler):
    def __float__(self):
        return float(average(self))

    def __int__(self):
        if len(self) < self.maxlen:
            return 0

        last = self[-1]
        rest = average(itertools.islice(self, len(self) - 1))

        return int(last > rest) - int(last < rest)
