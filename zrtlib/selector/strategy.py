import operator as op
import itertools
import collections

from zrtlib import zutils
from zrtlib.selector.technique import Random

class IterableStack(list):
    def __init__(self, descending=True):
        self.order = 0 if descending else -1

    def __iter__(self):
        return self

    def __next__(self):
        if not self:
            raise StopIteration()

        last = self[-1]
        item = last.pop(self.order)
        if not last:
            self.pop()

        return item

    def push(self, iterable):
        self.append(list(iterable))

class SelectionStrategy:
    def pick(self, documents, feedback=None):
        raise NotImplementedError()

    def stream(self, documents, feedback=None):
        while True:
            yield self.pick(documents, feedback)

class BlindHomogenous(SelectionStrategy):
    def __init__(self, technique, **kwargs):
        self.technique = technique
        self.kwargs = kwargs

    def pick(self, documents, feedback=None):
        try:
            return next(self.technique)
        except TypeError: # http://stackoverflow.com/a/1549854
            self.technique = self.technique(documents, **self.kwargs)
            return self.pick(documents, feedback)

class CoOccurrence(BlindHomogenous):
    def __init__(self, feedback, radius=1, technique=Random, **kwargs):
        self.feedback = feedback
        self.radius = radius

        self.stack = IterableStack()
        self.blind = BlindHomogenous(technique, **kwargs)

    def pick(self, documents, feedback=None):
        if feedback is not None:
            memory = float(self.feedback)

            if feedback > memory:
                last = documents['selected'].argmax()
                term = documents.iloc[last]['term']
                matches = documents[documents['term'] == term]
                self.stack.push(self.proximity(documents, matches))
            elif memory > feedback:
                self.stack.pop()

            self.feedback.append(feedback)

        iterable = (self.stack, self.blind.stream(documents))
        for i in itertools.chain.from_iterable(iterable):
            matches = documents[documents['term'] == i]
            if not matches['selected'].any():
                return i

    def proximity(self, documents, matches):
        occurence = collections.Counter()

        for i in matches.itertuples():
            docs = documents[documents['document'] == i.document]
            for (term, distance) in self.proximity_(i, docs):
                occurence[term['term']] += 1 / distance

        yield from map(op.itemgetter(0), occurence.most_common())

    def proximity_(self, row, documents):
        raise NotImplementedError()

class DirectNeighbor(CoOccurrence):
    def proximity_(self, row, documents):
        start = max(0, row.Index - self.radius)
        stop = min(len(documents), row.Index + self.radius + 1)

        for i in range(start, stop):
            distance = abs(row.Index - i)
            if distance != 0:
                yield (documents.iloc[i], distance)

class NearestNeighbor(CoOccurrence):
    def proximity_(self, row, documents):
        for step in (1, -1):
            yield from self.navigate(row, documents, self.radius, step)

    def navigate(self, row, documents, depth, step):
        if depth < 1:
            return

        reference = set(zutils.count(row.start, row.end))

        for i in itertools.count(row.Index + step, step):
            if i < 0 or i >= len(documents):
                break

            current = documents.iloc[i]
            coverage = set(zutils.count(current['start'], current['end']))
            if reference.isdisjoint(coverage):
                yield (current, self.radius - depth + 1)
                yield from self.navigate(current, documents, depth - 1, step)
                break

class RegionNeighbor(CoOccurrence):
    def proximity_(self, row, documents):
        regions = documents.groupby('region')

        for step in (1, -1):
            start = row['region'] + step
            stop = step * self.radius + 1

            for (i, r) in enumerate(range(start, stop, step), 1):
                if r not in regions.groups:
                    break
                selection = regions.get_group(r)

                #
                # The longest term within a region is the most
                # important.
                #
                longest = None
                for j in selection.itertuples():
                    if longest is None:
                        longest = j
                    else:
                        known = longest.end - longest.start
                        current = j.end - j.start
                        if current > known:
                            longest = j

                yield (longest, i)