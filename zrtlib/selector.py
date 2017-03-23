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
        # pass on to strategy
        try:
            term = self.strategy.pick(self.df, self.feedback)
        except LookupError:
            raise StopIteration()

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

########################################################################

class SelectionStrategy:
    @classmethod
    def build(cls, request, **kwargs):
        constructor = {
            'tf': TermFrequency,
            'df': DocumentFrequency,
            'random': Random,
            'entropy': Entropy,
            'relevance': Relevance,
        }
        if request in constructor:
            return BlindHomogenous(constructor[request], **kwargs)

        raise LookupError()

    def unselected(self, documents):
        return documents[documents['selected'] == 0]

    def pick(self, documents, feedback=None):
        remaining = self.unselected(documents)
        if remaining.empty:
            raise LookupError()

        return next(self.choose(documents, feedback))

    def choose(self, documents, feedback=None):
        raise NotImplementedError()

class BlindHomogenous(SelectionStrategy):
    def __init__(self, technique, **kwargs):
        super().__init__()

        self.technique = technique
        self.kwargs = kwargs

    def choose(self, documents, feedback=None):
        return self.technique(self.unselected(documents), **self.kwargs)

########################################################################

class SelectionTechnique:
    def __init__(self, documents):
        self.documents = documents

    def __next__(self, documents):
        raise NotImplementedError()

class Random(SelectionTechnique):
    def __init__(self, documents, weighted=False, seed=None):
        super().__init__(documents)

        self.weights = 'term' if weighted else None
        self.seed = seed

    def __next__(self):
        df = (self.documents['term'].
              value_counts().
              reset_index().
              sample(weights=self.weights, random_state=self.seed))

        return df['index'].iloc[0]

class Frequency(SelectionTechnique):
    def __next__(self):
        return self.then().value_counts().argmax()

    def then(self):
        raise NotImplementedError()

class DocumentFrequency(Frequency):
    def then(self):
        groups = self.documents.groupby('document')
        return groups['term'].apply(lambda x: pd.Series(x.unique()))

class TermFrequency(Frequency):
    def then(self):
        return self.documents['term']

class Relevance(SelectionTechnique):
    def __init__(self, documents, query, relevant):
        super().__init__(documents)

        self.query = query
        self.relevant = relevant

    def __next__(self):
        rels = self.documents[self.documents['document'].isin(self.relevant)]
        elegible = rels.merge(self.query,
                              left_on='term',
                              right_on=HiddenDocument.columns['visible'],
                              copy=False)

        return next(DocumentFrequency(elegible))

# http://www.cs.bham.ac.uk/~pxt/IDA/term_selection.pdf
class Entropy(SelectionTechnique):
    def __next__(self):
        groups = self.documents.groupby('document')

        f = lambda x: pd.Series(x.value_counts(normalize=True))
        df = groups['term'].apply(f).reset_index(level=0, drop=True)
        df = df.groupby(df.index).aggregate(st.entropy)

        return df.argmax()
