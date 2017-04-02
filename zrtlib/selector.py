import operator as op
import collections

import numpy as np
import pandas as pd
import scipy.stats as st

from zrtlib import logger
from zrtlib.stack import IterableStack
from zrtlib.document import HiddenDocument

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
        self.mark_selected(term)

        return term

    #
    # mark the term as being selected
    #
    def mark_selected(self, term, order=None):
        matches = self.df['term'] == term
        if matches.empty:
            return

        if order is None:
            order = self.df['selected'].max() + 1
        self.df.loc[matches, 'selected'] = order

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

        raise LookupError(request)

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

class CoOccurrence(BlindHomogenous):
    def __init__(self, feedback, radius=1, technique=Entropy, **kwargs):
        super().__init__(technique, **kwargs)

        self.feedback = feedback
        self.radius = radius
        self.stack = IterableStack()

    def choose(self, documents, feedback=None):
        if feedback is not None:
            memory = float(self.feedback)

            if feedback > memory:
                last = documents['selected'].argmax()
                term = documents.iloc[last]['term']
                matches = documents[documents['term'] == term]
                self.stack.push(self.proximity(documents, matches))
            elif memory > feedback:
                self.stack.peel()

            self.feedback.append(feedback)

        while self.stack:
            choice = self.stack.pop()
            matches = documents[documents['term'] == choice]
            if not matches['selected'].any():
                return choice

        return super().choose(documents)

    def discount(self, x):
        return 1 / x

    def proximity(self, documents, matches):
        raise NotImplementedError()

class DirectNeighbor(CoOccurrence):
    def proximity(self, documents, matches):
        occurence = collections.Counter()

        for i in matches.itertuples():
            start = max(0, i.Index - self.radius)
            stop = min(len(documents), i.Index + self.radius + 1)
            for j in range(start, stop):
                factor = abs(i.Index - j)
                if factor != 0:
                    term = documents.iloc[j]
                    occurence[term['term']] += self.discount(factor)

        yield from map(op.itemgetter(0), occurence.most_common())

########################################################################

class FeedbackHandler(collections.deque):
    def __init__(self, n=1):
        super().__init__(maxlen=n)

    def __float__(self):
        raise NotImplementedError()

class RecentWeighted:
    def __float__(self):
        np.average(self, weights=np.linspace(0, 1, len(self)))

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

# http://www.cs.bham.ac.uk/~pxt/IDA/term_selection.pdf
class Entropy(SelectionTechnique):
    def __next__(self):
        groups = self.documents.groupby('document')

        f = lambda x: pd.Series(x.value_counts(normalize=True))
        df = groups['term'].apply(f).reset_index(level=0, drop=True)
        df = df.groupby(df.index).aggregate(st.entropy)

        return df.argmax()

class Relevance(SelectionTechnique):
    def __init__(self, documents, query, relevant):
        super().__init__(documents)

        self.query = query.df[HiddenDocument.columns['visible']]
        self.relevant = relevant

    def __next__(self):
        df = self.documents[self.documents['document'].isin(self.relevant)]
        df = df[df['term'].isin(self.query)]
        if df.empty:
            raise LookupError()

        return next(Entropy(df))
