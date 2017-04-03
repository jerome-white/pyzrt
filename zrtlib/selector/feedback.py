import collections

import numpy as np

class FeedbackHandler(collections.deque):
    def __init__(self, n=1):
        super().__init__(maxlen=n)

    def __float__(self):
        raise NotImplementedError()

class RecentWeighted:
    def __float__(self):
        np.average(self, weights=np.linspace(0, 1, len(self)))
