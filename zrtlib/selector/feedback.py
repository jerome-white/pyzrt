import collections

import numpy as np

class FeedbackHandler(collections.deque):
    def __init__(self, maxlen=1):
        super().__init__(maxlen=maxlen)

    def __float__(self):
        raise NotImplementedError()

class RecentWeighted(FeedbackHandler):
    def __float__(self):
        weights = np.linspace(1, 2, len(self))

        return np.average(self, weights=weights) if weights.size > 0 else 0.0
