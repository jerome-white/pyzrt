import random
import operator as op
from collections import Counter, defaultdict

import pandas as pd
import scipy.stats as st

from zrtlib import logger
from zrtlib.indri import QueryRelevance

Entry = namedtuple('Entry', 'doc, relevant')

def Selector(x, **kwargs):
    return {
        'random': RandomSelector,
        'df': DocumentFrequency,
        'tf': TermFrequency,
        'entropy': Entropy,
        'relevance': Relevance,
    }[x](**kwargs)

class SelectionManager:
    def __init__(self, strategy):
        self.strategy_manager = strategy

        self.df = None
        self.feedback = None
        self.documents = {}
        self.columns = { 'hidden': 'term', 'unhidden': 'original' }

    def __iter__(self):
        self.df = pd.concat(self.documents.values(), copy=False)
        # conceal the documents
        key = self.columns['hidden']
        self.df[key] = self.df.apply(lambda x: x[key][::-1], axis=1)

        return self

    def __next__(self):
        selector = self.strategy_manager.get_selector(self.feedback)
        try:
            term = selector.pick(self.df)
        except LookupError:
            raise StopIteration()

        # flip the term
        matches = self.df[self.columns['unhidden']] == term
        self.df.loc[matches, self.columns['hidden']] = term

        return term

    def add(self, document):
        assert(document.name not in self.documents)

        new_columns = {
            'name': document.name,
            'relevant': None,
            'actual': lambda x: x.term,
        }
        self.documents[document.name] = document.df.assign(**new_columns)

    #
    # Make the selector aware of relevant documents. Should only be
    # implemented in cases where the selector is also an oracle.
    #
    def divulge(self, qrels):
        relevant = QueryRelevance(qrels)
        for (name, df) in self.documents.items():
            if name in relevants:
                df.relevant = True

class TermSelector:
    def __iter__(self):
        raise NotImplementedError()

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
            raise NotImplementedError()

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

class Relevance(Frequency):
    def __init__(self):
        super().__init__()
        self.documents = {}

    def add(self, document):
        assert(document.name not in self.documents)
        self.documents[document.name] = document.df.term.values

    def divulge(self, qrels, query):
        log = logger.getlogger()

        document_terms = Counter()
        relevant = QueryRelevance(qrels)
        for i in relevant.documents:
            if i not in self.documents:
                log.warning('{0} not in corpus'.format(i))
                continue
            document_terms.update(self.documents[i])
        log.debug('document terms: {0}'.format(len(document_terms)))

        query_terms = Counter(query.df.pt.values)
        log.debug('query terms: {0}'.format(len(query_terms)))

        common = set(query_terms.keys())
        common.intersection_update(document_terms.keys())
        assert(common)

        self.counter = Counter()
        for i in (document_terms, query_terms):
            self.counter.update({ x: i[x] for x in common })

# http://www.cs.bham.ac.uk/~pxt/IDA/term_selection.pdf
class Entropy(TermSelector):
    def __init__(self):
        super().__init__()
        self.relative_tf = defaultdict(list)

    def __iter__(self):
        ent = { x: st.entropy(y) for (x, y) in self.relative_tf.items() }

        df = pd.Series(ent)
        df.sort_values(ascending=False, inplace=True)

        yield from df.index

    def add(self, document):
        counts = document.df.term.value_counts()
        terms = counts.sum()

        for (term, appearances) in counts.iteritems():
            prob = appearances / terms
            self.relative_tf[term].append(prob)
