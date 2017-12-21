import collections as cl

_Term = cl.namedtuple('_Term', 'name, ngram, position')

class Term(_Term):
    def __new__(cls, name, ngram, position):
        return super(Term, cls).__new__(cls, name, ngram, position)

    def __init__(self, name, ngram, position):
        self.span = self.position + len(self) - 1

    def __len__(self):
        return len(self.ngram)

    def __lt__(self, other):
        if self.position == other.position:
            return len(self) < len(other)
        return self.position < other.position

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.ngram

    @classmethod
    def _fromdict(cls, dictionary):
        d = { x: dictionary[x] for x in cls._fields }
        d['position'] = int(d['position'])

        return cls(**d)
