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

########################################################################

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

    def unselected(self, documents):
        return documents[documents['selected'] == 0]
    
    def pick(self, documents, feedback=None):
        remaining = self.unselected(documents)
        if remaining.empty:
            raise LookupError()
        
        return self.pick_(documents, feedback)

class BlindHomogenousStrategy(SelectionStrategy):
    def __init__(self, technique):
        super().__init__()
        self.technique = technique

    def pick_(self, documents, feedback=None):
        return self.technique.pick(self.unselected(documents))

########################################################################

class SelectionTechnique:
    def pick(self, documents):
        raise NotImplementedError()
    
class Random(SelectionTechnique):
    def __init__(self, weighted=False, seed=None):
        super().__init__()

        self.weights = 'term' if weighted else None        
        self.seed = seed

    def pick(self, documents):
        df = (documents['term'].
              value_counts().
              reset_index().
              sample(weights=self.weights, random_state=self.seed))

        return df['index'].iloc[0]

class Frequency(SelectionTechnique):
    def pick(self, documents):
        df = self.pick_(documents, feedback)

        return df.value_counts().argmax()

    def pick_(self, documents):
        raise NotImplementedError()

class DocumentFrequency(Frequency):
    def pick_(self, documents):
        groups = documents.groupby('document')
        return groups['term'].apply(lambda x: pd.Series(x.unique()))

class TermFrequency(Frequency):
    def pick_(self, documents):
        return documents['term']

class Relevance(SelectionTechnique):
    def __init__(self, query, relevant):
        super().__init__()
        self.query = query
        self.relevant = relevant

    def pick(self, documents):
        rels = documents[documents['document'].isin(self.relevant)]
        elegible = rels.merge(self.query,
                              left_on='term',
                              right_on=HiddenDocument.columns['visible'],
                              copy=False)

        return Random().pick(elegible)

# http://www.cs.bham.ac.uk/~pxt/IDA/term_selection.pdf
class Entropy(SelectionTechnique):
    def pick(self, documents):
        groups = documents.groupby('document')

        f = lambda x: pd.Series(x.value_counts(normalize=True))
        df = groups['term'].apply(f).reset_index(level=0, drop=True)
        df = df.groupby(df.index).aggregate(st.entropy)

        return df.argmax()
