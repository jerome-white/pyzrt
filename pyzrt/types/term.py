import collections as clc

BasicTerm = clc.namedtuple('BasicTerm', 'name, ngram, position')

class Term(BasicTerm):
    def __new__(cls, name, ngram, position):
        self = super(Term, cls).__new__(cls, name, ngram, position)
        return self

    def __len__(self):
        return len(self.ngram)

    def __lt__(self, other):
        if self.position == other.position:
            return len(self) < len(other)
        return self.position < other.position

    def __sub__(self, other):
        return other.position - self.end()

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.ngram

    def end(self):
        return self.position + len(self)
