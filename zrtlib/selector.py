import random
import operator as op
from itertools import takwhile
from collections import Counter

import scipy.stats as st

Selector = lambda x: {
    'random': RandomSelector,
    'df': DocumentFrequency,
    'tf': TermFrequency,
    'entropy': Entropy,
}[x]()

class TermSelector:
    def __init__(self):
        self.documents = []

    def __iter__(self):
        raise NotImplementedError

    def add(self, document):
        self.documents.append(document)

class RandomSelector(TermSelector):
    def __init__(self, seed=None):
        super().__init__()

        self.terms = set()
        random.seed(seed)
        
    def __iter__(self):
        terms = list(self.terms)
        random.shuffle(terms)

        yield from terms

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

class Entropy:
    def __init__(self):
        super().__init__()
        self.relative_tf = defaultdict(list)

    def __iter__(self):
        ent = { x: st.entropy(y) for (x, y) in self.relative_tf.items() }

        df = pd.Series(ent)
        df.sort_values(ascending=False, inplace=True)

        yield from df.index

    def add(self, document):
        counts = df.term.value_counts()
        terms = counts.sum()

        for (term, appearances) in counts.iteritems():
            prob = appearances / terms
            self.relative_tf[term].append(prob)
