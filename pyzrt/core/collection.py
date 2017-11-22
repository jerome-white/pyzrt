import csv
import operator as op
import itertools as it

from pyzrt.core.term import Term

class TermCollection(list):
    def __init__(self, collection=None):
        self.collection = collection

        if self.collection:
            with self.collection.open() as fp:
                self.extend(map(Term._fromdict, csv.DictReader(fp)))
            self.sort()

    def __repr__(self):
        return self.collection.stem if self.collection else ''

    def __str__(self):
        return self.tostring(str)

    def tostring(self, how, separator=' '):
        return separator.join(map(how, self))

    def bylength(self, descending=True):
        self.sort(key=len, reverse=descending)

    def get(self, ngram):
        for (i, term) in enumerate(self):
            if term.ngram == ngram:
                yield (i, term)

    def regions(self, start=0, follows=None):
        if follows is None:
            follows = lambda x, y: x.position > y.span

        region = TermCollection()

        for current in it.islice(self, start, None):
            if region:
                previous = region[-1]
                assert(previous.position <= current.position) # not in order!
                if follows(current, previous):
                    yield region
                    region = TermCollection()
            region.append(current)

        if region:
            yield region

    def after(self, index):
        ptr = self[index]
        follows = lambda x, y: x.position > ptr.span

        for i in it.islice(self, index, None):
            if i.position > ptr.position:
                break
            index += 1

        yield from next(self.regions(index, follows))

    def tocsv(self, fp, header=True):
        writer = csv.DictWriter(fp, fieldnames=Term._fields)
        if header:
            writer.writeheader()
        writer.writerows(map(op.methodcaller('_asdict'), self))
