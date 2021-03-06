import operator as op
import itertools
import collections

from pyzrt.util import logger

def stream(items, move=next, stop=None, compare=op.eq):
    '''Iterate through a sequence that doesn't strictly conform to
    Python's iterable semantics.

    '''

    while True:
        i = move(items)
        if compare(i, stop):
            break
        yield i

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
        attachment = list(iterable)
        if not attachment:
            raise ValueError()
        self.append(attachment)

    def peel(self):
        if self:
            self.pop()

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

class FromFeedback(SelectionStrategy):
    def __init__(self, sieve, technique):
        self.sieve = sieve
        self.blind = BlindHomogenous(technique)
        self.stack = IterableStack()

    def pick(self, documents, feedback):
        improvement = int(feedback)

        if improvement > 0:
            # get the last term that was guessed
            last = documents['selected'].argmax()
            term = documents.ix[last]['term']

            # find documents to explore based on that term
            relevant = self.sieve.like(term, documents)

            # find terms to explore based on those documents
            potentials = self.proximity(term, relevant)

            # add those terms to the stack
            try:
                self.stack.push(potentials)
            except ValueError:
                log = logger.getlogger()
                log.warning('Unable to add potential values')
        elif improvement < 0:
            self.stack.peel()

        eligible = documents[documents['selected'] == 0]
        iterable = (self.stack, stream(eligible, self.blind.pick))
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
        yield from stream(self.technique(documents))

class CoOccurrence(FromFeedback):
    def __init__(self, sieve, technique, radius=1):
        super().__init__(sieve, technique)

        self.radius = radius

    def proximity(self, term, documents):
        occurrence = collections.Counter()

        for (_, df) in documents.groupby('document', sort=False):
            rows = df[df['term'] == term]
            for i in rows.itertuples():
                position = df.index.get_loc(i.Index)
                for (neighbor, distance) in self._proximity(position, df):
                    occurrence[neighbor['term']] += 1 / distance

        yield from map(op.itemgetter(0), occurrence.most_common())

    def _proximity(self, row, documents):
        raise NotImplementedError()

class DirectNeighbor(CoOccurrence):
    def _proximity(self, position, documents):
        start = max(0, position - self.radius)
        stop = min(len(documents), position + self.radius + 1)

        for i in range(start, stop):
            distance = abs(position - i)
            if distance != 0:
                yield (documents.iloc[i], distance)

class NearestNeighbor(CoOccurrence):
    def _proximity(self, position, documents):
        for step in (1, -1):
            yield from self.navigate(position, documents, self.radius, step)

    @staticmethod
    def window(position, documents):
        row = documents.iloc[position]
        return set(range(row['start'], row['end'] + 1))

    def navigate(self, position, documents, depth, step):
        if depth < 1 or position < 0 or position >= len(documents):
            return

        reference = NearestNeighbor.window(position, documents)

        for i in itertools.count(position + step, step):
            if i < 0 or i >= len(documents):
                break

            current = NearestNeighbor.window(i, documents)
            if reference.isdisjoint(current):
                yield (documents.iloc[i], self.radius - depth + 1)
                yield from self.navigate(i, documents, depth - 1, step)
                break

class RegionNeighbor(CoOccurrence):
    def _proximity(self, position, documents):
        row = documents.iloc[position]
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
