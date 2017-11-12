import csv
import operator as op
import itertools as it
import collections as clc

TermAttributes = clc.namedtuple('TermAttributes', 'pseudoterm, ngram, offset')

class Term(TermAttributes):
    def __new__(cls, pseudoterm, ngram, offset):
        self = super(Term, cls).__new__(cls, pseudoterm, ngram, offset)
        return self

    def __len__(self):
        return len(self.ngram)

    def __lt__(self, other):
        if self.offset == other.offset:
            return len(self) < len(other)
        return self.offset < other.offset

    def __sub__(self, other):
        return other.offset - self.end()

    def __str__(self):
        return self.pseudoterm

    def end(self):
        return self.offset + len(self)

class TermCollection(list):
    def __init__(self, path=None):
        self.path = path
        self.inorder = True

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

    def bylength(self, descending=True):
        self.sort(key=len, reverse=descending)
        self.inorder = False

    def get(self, ngram):
        for (i, term) in enumerate(self):
            if term.ngram == ngram:
                yield (i, term)

    def subset(self, difference, start=0, limit=0):
        assert(self.inorder)

        region = TermCollection()

        for term in it.islice(self, start, None):
            if region and difference(region[-1], term) > 0:
                yield region
                region = TermCollection()

                limit -= 1
                if not limit:
                    break
            region.append(term)

        if limit and region:
            yield region

    def regions(self):
        yield from self.subset(op.sub)

    def immediates(self, index):
        difference = lambda x, y: self[index] - y

        yield from next(self.subset(difference, index + 1, 1))
