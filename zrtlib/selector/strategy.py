import operator as op
import itertools
import collections

from zrtlib import zutils

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
    def pick(self, documents, feedback):
        raise NotImplementedError()

class BlindHomogenous(SelectionStrategy):
    def __init__(self, technique):
        self.technique = technique

    def pick(self, documents, feedback=None):
        try:
            return next(self.technique)
        except TypeError: # http://stackoverflow.com/a/1549854
            self.technique = self.technique(documents)
            return self.pick(documents)

    def stream(self, documents):
        while True:
            choice = self.pick(documents)
            if choice is None:
                break
            yield choice

class FromFeedback(SelectionStrategy):
    def __init__(self, sieve, technique):
        self.sieve = sieve
        self.blind = BlindHomogenous(technique)
        self.stack = IterableStack()

    def pick(self, documents, feedback):
        improvement = int(feedback)

        if improvement > 0:
            last = documents['selected'].argmax()
            term = documents.iloc[last]['term']
            relevant = self.sieve.like(term, documents)
            self.stack.push(self.proximity(term, relevant))
        elif improvement < 0:
            self.stack.pop()

        eligible = documents[documents['selected'] == 0]
        iterable = (self.stack, self.blind.stream(eligible))
        for i in itertools.chain.from_iterable(iterable):
            matches = documents[documents['term'] == i]
            if not matches['selected'].any():
                return i

    def proximity(self, term, documents):
        raise NotImplementedError()

class BlindRelevance(FromFeedback):
    def __init__(self, sieve, technique, secondary_technique=None):
        if secondary_technique is None:
            secondary_technique = technique

        super().__init__(sieve, secondary_technique)
        self.technique = technique

    def proximity(self, term, documents):
        yield from self.technique(documents)

class CoOccurrence(FromFeedback):
    def __init__(self, sieve, technique, radius=1):
        super().__init__(sieve, technique)

        self.radius = radius

    def proximity(self, term, documents):
        occurrence = collections.Counter()

        for df in documents:
            rows = df[df['term'] == term]
            for i in rows.itertuples():
                for (neighbor, distance) in self._proximity(i, df):
                    occurrence[neighbor['term']] += 1 / distance

        yield from map(op.itemgetter(0), occurrence.most_common())

    def _proximity(self, row, documents):
        raise NotImplementedError()

class DirectNeighbor(CoOccurrence):
    def _proximity(self, row, documents):
        start = max(0, row.Index - self.radius)
        stop = min(len(documents), row.Index + self.radius + 1)

        for i in range(start, stop):
            distance = abs(row.Index - i)
            if distance != 0:
                yield (documents.iloc[i], distance)

class NearestNeighbor(CoOccurrence):
    def _proximity(self, row, documents):
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
    def _proximity(self, row, documents):
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
