import operator as op
import collections

import zrtlib.selector.technique as tek

class IterableStack:
    def __init__(self):
        self.stack = []

    def __bool__(self):
        return bool(self.stack)
    
    def push(self, item):
        self.stack.append(list(item))

    def pop(self):
        if not self:
            raise BufferError()

        last = self.stack[-1]
        item = last.pop(0)
        if not last:
            self.peel()

        return item

    def peel(self):
        if self:
            self.stack.pop()

class SelectionStrategy:
    @classmethod
    def build(cls, request, **kwargs):
        constructor = {
            'tf': tek.TermFrequency,
            'df': tek.DocumentFrequency,
            'random': tek.Random,
            'entropy': tek.Entropy,
            'relevance': tek.Relevance,
        }
        if request in constructor:
            return BlindHomogenous(constructor[request], **kwargs)

        constructor = {
            'direct': tek.DirectNeighbor,
        }
        if request in constructor:
            return constructor[request](**kwargs)

        raise LookupError(request)

    def unselected(self, documents):
        return documents[documents['selected'] == 0]

    def pick(self, documents, feedback=None):
        remaining = self.unselected(documents)
        if remaining.empty:
            raise LookupError()

        return next(self.choose(documents, feedback))

    def choose(self, documents, feedback=None):
        raise NotImplementedError()

class BlindHomogenous(SelectionStrategy):
    def __init__(self, technique, **kwargs):
        super().__init__()

        self.technique = technique
        self.kwargs = kwargs

    def choose(self, documents, feedback=None):
        return self.technique(self.unselected(documents), **self.kwargs)

class CoOccurrence(BlindHomogenous):
    def __init__(self, feedback, radius=1, technique=tek.Entropy, **kwargs):
        super().__init__(technique, **kwargs)

        self.feedback = feedback
        self.radius = radius
        self.stack = IterableStack()

    def choose(self, documents, feedback=None):
        if feedback is not None:
            memory = float(self.feedback)

            if feedback > memory:
                last = documents['selected'].argmax()
                term = documents.iloc[last]['term']
                matches = documents[documents['term'] == term]
                self.stack.push(self.proximity(documents, matches))
            elif memory > feedback:
                self.stack.peel()

            self.feedback.append(feedback)

        while self.stack:
            choice = self.stack.pop()
            matches = documents[documents['term'] == choice]
            if not matches['selected'].any():
                return choice

        return super().choose(documents)

    def discount(self, x):
        return 1 / x

    def proximity(self, documents, matches):
        raise NotImplementedError()

class DirectNeighbor(CoOccurrence):
    def proximity(self, documents, matches):
        occurence = collections.Counter()

        for i in matches.itertuples():
            start = max(0, i.Index - self.radius)
            stop = min(len(documents), i.Index + self.radius + 1)
            for j in range(start, stop):
                factor = abs(i.Index - j)
                if factor != 0:
                    term = documents.iloc[j]
                    occurence[term['term']] += self.discount(factor)

        yield from map(op.itemgetter(0), occurence.most_common())
