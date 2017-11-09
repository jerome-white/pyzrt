import csv
import operator as op
import collections as clc

class Term:
    def __init__(self, name, ngram, offset):
        self.name = name
        self.ngram = ngram
        self.offset = offset

    def __len__(self):
        return len(self.ngram)

    def __lt__(self, other):
        if self.offset == other.offset:
            return len(self) < len(other)
        return self.offset < other.offset

    def __sub__(self, other):
        return (self.offset + len(self)) - other.offset

    def __str__(self):
        return self.name

class TermCollection(list):
    def __init__(self, path=None):
        self.path = path

        if self.path:
            with self.path.open() as fp:
                for line in csv.DictReader(fp):
                    offset = int(int(line['start']))
                    term = Term(line['term'], line['ngram'], offset)
                    self.append(term)
            self.sort()

    def __repr__(self):
        return self.path.stem if self.path else ''

    def __str__(self):
        return ' '.join(map(op.attrgetter('ngram'), self))

    def get(self, ngram):
        for (i, term) in enumerate(self):
            if term.ngram == ngram:
                yield (i, term)

    def regions(self):
        region = TermCollection()

        for i in self:
            if region and region[-1] - i < 0:
                yield region
                region = TermCollection()
            region.append(i)

        if region:
            yield region
