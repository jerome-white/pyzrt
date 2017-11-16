import csv
import operator as op
import itertools as it

from . import Term

class TermCollection(list):
    def __init__(self, collection=None):
        self.collection = collection
        self.inorder = True

        if self.collection:
            with self.collection.open() as fp:
                for line in csv.DictReader(fp):
                    position = int(line['position'])
                    term = Term(line['name'], line['ngram'], position)
                    self.append(term)
            self.sort()

    def __repr__(self):
        return self.collection.stem if self.collection else ''

    def __str__(self):
        return ' '.join(map(op.attrgetter('ngram'), self))

    def bylength(self, descending=True):
        self.sort(key=len, reverse=descending)
        self.inorder = False

    def get(self, ngram):
        for (i, term) in enumerate(self):
            if term.ngram == ngram:
                yield (i, term)

    def subset(self, difference, start=0):
        assert(self.inorder)

        region = TermCollection()

        for term in it.islice(self, start, None):
            if region and difference(region[-1], term) > 0:
                yield region
                region = TermCollection()
            region.append(term)

        if region:
            yield region

    def regions(self):
        yield from self.subset(op.sub)

    def immediates(self, index):
        difference = lambda x, y: self[index] - y

        yield from next(self.subset(difference, index + 1))

    def tocsv(self, fp, header=True):
        writer = csv.DictWriter(fp, fieldnames=Term._fields)
        if header:
            writer.writeheader()
        writer.writerows(map(op.methodcaller('_asdict'), self))
