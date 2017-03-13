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
    columns = { 'hidden': 'term', 'unhidden': 'original' }
    
    def __init__(self, strategy):
        self.strategy = strategy
        self.df = None
        self.feedback = None
        self.documents = {}

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
        df = self.df[self.columns['unhidden'] != self.columns['hidden']]
        term = self.strategy.pick(df, self.feedback)
        if term is None:
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
            'document': document.name,
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

class SelectionStrategy:
    def pick(self, documents, feedback=None):
        raise NotImplementedError()

class RandomSelector(SelectionStrategy):
    def __init__(self, weighted=False, seed=None):
        super().__init__()

        self.weighted = weighted
        self.seed = seed

    def pick(self, documents, feedback=None):
        index = TermSelector.columns['hidden']
        terms = documents[index].value_counts().reset_index()

        weights = index if self.weighted else None
        selection = documents.sample(n=1, weights=weights,
                                     random_state=self.seed)

        if not selection.empty:
            return selection['index'].iloc[0]

class Frequency(SelectionStrategy):
    def __init__(self, descending=True):
        self.ascending = not descending

    def pick(self, documents, feedback=None):
        df = self.pick_(documents, feedback)
        df = value_counts().sort_values(ascending=self.ascending).reset_index()
        
        return df['index'].iloc[0]
    
class DocumentFrequency(Frequency):
    def __init__(self, descending=False):
        super().__init__()
        
    def pick_(self, documents, feedback=None):
        groups = documents.groupby('document')
        return groups['term'].apply(lambda x: pd.Series(x.unique()))

class TermFrequency(Frequency):
    def __init__(self):
        super().__init__()

    def pick_(self, documents, feedback=None):
        return documents['term']

###

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
