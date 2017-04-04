import operator as op
import collections

from zrtlib import zutils
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
    def __init__(self, feedback, technique, radius=1, **kwargs):
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

    def proximity(self, documents, matches):
        occurence = collections.Counter()

        for i in matches.itertuples():
            docs = documents[documents['document'] == i.document]
            for (term, distance) in self.proximity_(i, docs):
                occurence[term['term']] += 1 / distance

        yield from map(op.itemgetter(0), occurence.most_common())

class DirectNeighbor(CoOccurrence):
    def proximity_(self, row, documents):
        start = max(0, row.Index - self.radius)
        stop = min(len(documents), row.Index + self.radius + 1)

        for i in range(start, stop):
            distance = abs(row.Index - j)
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
            stop = step * self.depth + 1
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
