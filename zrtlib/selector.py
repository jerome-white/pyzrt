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
    def __init__(self):
        self.df = None
        self.feedback = None
        self.documents = {}
        self.columns = { 'hidden': 'term', 'unhidden': 'original' }

    #
    # Set up the DataFrame used by the selectors
    #
    def __iter__(self):
        self.df = pd.concat(self.documents.values(), copy=False)

        # conceal the documents
        key = self.columns['hidden']
        self.df[key] = self.df.apply(lambda x: x[key][::-1], axis=1)

        return self

    #
    # Each iteration presents the dataframe to the strategy manager
    #
    def __next__(self):
        try:
            term = self.pick()
        except LookupError:
            raise StopIteration()

        # flip the term
        matches = self.df[self.columns['unhidden']] == term
        self.df.loc[matches, self.columns['hidden']] = term

        return term

    #
    # Make the selector aware of relevant documents.
    #
    def add(self, document):
        assert(document.name not in self.documents)

        new_columns = {
            'name': document.name,
            'relevant': None,
            'actual': lambda x: x.term,
        }
        self.documents[document.name] = document.df.assign(**new_columns)

    #
    # Make the selector aware of relevant documents.
    #
    def divulge(self, qrels, topic):
        for i in relevants(qrels, topic):
            if i in self.documents:
                self.document[i]['relevant'] = True

    #
    # Remove irrelevant documents
    #
    def purge(self):
        irrelevant = set()
        for (i, j) in self.documents:
            if not j.relevant.all():
                irrelevant.add(i)

        for i in irrelevant:
            del self.documents[i]
        
    def pick(self):
        raise NotImplementedError()

class HomogeneousSelectionManager
    def __init__(self, selector):
        super().__init__()
        self.selector = selector

    def pick(self):
        return next(self.selector(self.df))
    
class TermSelector:
    def __next__(self):
        raise NotImplementedError()

class RandomSelector(TermSelector):
    def __init__(self, documents, weighted=False, seed=None):
        super().__init__()

        index = self.columns['hidden']
        self.terms = documents[index].value_counts().reset_index()

        self.weights = None if not weighted else index
        self.seed = seed

    def __next__(self):
        selection = self.terms.sample(n=1, weights=self.weights,
                                      random_state=self.seed)
        return selection['index'].iloc[0]

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
