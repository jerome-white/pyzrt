import pandas as pd
import scipy.stats as st

import numpy as np
import pandas as pd

from zrtlib import logger

class TermSelector:
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

        return self

    #
    # Each iteration presents the dataframe to the strategy manager
    #
    def __next__(self):
        # obtain the unselected terms
        unselected = self.df[self.df['selected'] == 0]
        if unselected.empty:
            raise StopIteration()

        # pass on to strategy
        term = self.strategy.pick(unselected, self.feedback)

        # mark the term as being selected
        matches = self.df['term'] == term
        self.df.loc[matches, 'selected'] = self.df['selected'].max() + 1

        return term

    #
    # Add documents to the corpus
    #
    def add(self, document):
        assert(document.name not in self.documents)

        new_columns = {
            'document': document.name,
            'selected': 0,
        }
        self.documents[document.name] = document.df.assign(**new_columns)

    #
    # Remove certain documents from the database
    #
    def purge(self, documents):
        for i in documents:
            if i in self.documents:
                del self.documents[i]

    def keep_only(self, documents):
        rels = set(documents)
        docs = set(self.documents.keys())

        self.purge(docs.difference(rels))

class SelectionStrategy:
    @classmethod
    def build(cls, strategy, **kwargs):
        return {
            'random': Random,
            'df': DocumentFrequency,
            'tf': TermFrequency,
            'entropy': Entropy,
            'relevance': Relevance,
        }[strategy](**kwargs)

    def pick(self, documents, feedback=None):
        raise NotImplementedError()

class Random(SelectionStrategy):
    def __init__(self, weighted=False, seed=None):
        super().__init__()

        self.weighted = weighted
        self.seed = seed

    def pick(self, documents, feedback=None):
        weights = 'term' if self.weighted else None
        df = (documents['term'].
              value_counts().
              reset_index().
              sample(weights=weights, random_state=self.seed))

        return df['index'].iloc[0]

class Frequency(SelectionStrategy):
    def pick(self, documents, feedback=None):
        df = self.pick_(documents, feedback)

        return df.value_counts().argmax()

    def pick_(self, documents, feedback=None):
        raise NotImplementedError()

class DocumentFrequency(Frequency):
    def pick_(self, documents, feedback=None):
        groups = documents.groupby('document')
        return groups['term'].apply(lambda x: pd.Series(x.unique()))

class TermFrequency(Frequency):
    def pick_(self, documents, feedback=None):
        return documents['term']

class Relevance(Frequency):
    def __init__(self, query):
        super().__init__()
        self.query = query

    def pick(self, documents, feedback=None):
        qterms = HiddenDocument.columns['visible']
        similar = np.intersect1d(documents['term'], self.query[qterms])

        return similar[0]

# http://www.cs.bham.ac.uk/~pxt/IDA/term_selection.pdf
class Entropy(SelectionStrategy):
    def pick(self, documents, feedback=None):
        groups = documents.groupby('document')

        f = lambda x: pd.Series(x.value_counts(normalize=True))
        df = groups['term'].apply(f).reset_index(level=0, drop=True)
        df = df.groupby(df.index).aggregate(st.entropy)

        return df.argmax()
