import operator as op
from collections import Counter

class TermSelector:
    def __init__(self):
        self.documents = []

    def __iter__(self):
        raise NotImplementedError

    def add(self, document):
        self.documents.append(document)

class RandomSelector(TermSelector):
    def __init__(self):
        super().__init__()
        
        self.terms = set()
        
    def __iter__(self):
        yield from self.terms

    def add(self, document):
        self.terms.update(document.df.term.values)

class Frequency(TermSelector):
    def __init__(self):
        super().__init__()

        self.tf = Counter()
        self.df = Counter()
        self.counter = None

    def __iter__(self):
        if self.counter is None:
            raise NotImplementedError

        yield from map(op.itemgetter(0), self.counter.most_common())

    def add(self, document):
        counts = document.df.term.value_counts().to_dict()

        self.tf.update(counts)
        self.df.update(counts.keys())

class DocumentFrequency(Frequency):
    def __init__(self):
        super().__init__()
        self.counter = self.df

class TermFrequency(Frequency):
    def __init__(self):
        super().__init__()
        self.counter = self.tf
