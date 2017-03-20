import pandas as pd
import scipy.stats as st

from zrtlib import logger

def Selector(x, **kwargs):
    return {
        'random': RandomSelector,
        'df': DocumentFrequency,
        'tf': TermFrequency,
        'entropy': Entropy,
        'relevance': Relevance,
    }[x](**kwargs)

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
        unselected = self.df[self.df['selected'] == False]
        if unselected.empty:
            raise StopIteration()

        # pass on to strategy
        term = self.strategy.pick(unselected, self.feedback)

        # flip the term
        matches = self.df['term'] == term
        self.df.loc[matches, 'selected'] = True

        return term

    #
    # Add documents to the corpus
    #
    def add(self, document):
        assert(document.name not in self.documents)

        new_columns = {
            'document': document.name,
            'relevant': None,
            'selected': False,
        }
        self.documents[document.name] = document.df.assign(**new_columns)

    #
    # Make the selector aware of relevant documents
    #
    def divulge(self, relevants):
        for i in relevants:
            if i in self.documents:
                self.documents[i]['relevant'] = True

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
    def __init__(self):
        self.tcol = TermSelector.columns['hidden']

    def pick(self, documents, feedback=None):
        raise NotImplementedError()

class Random(SelectionStrategy):
    def __init__(self, weighted=False, seed=None):
        super().__init__()

        self.weighted = weighted
        self.seed = seed

    def pick(self, documents, feedback=None):
        weights = 'term' if self.weighted else None
        df = (documents[self.tcol].
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
        return groups[self.tcol].apply(lambda x: pd.Series(x.unique()))

class TermFrequency(Frequency):
    def pick_(self, documents, feedback=None):
        return documents[self.tcol]

class Relevance(Frequency):
    def __init__(self, query):
        super().__init__()
        self.query = query

    def pick(self, documents, feedback=None):
        df = documents[documents['relevant'] == True]
        assert(not df.empty)
        similar = np.intersect1d(df[self.tcol], self.query[self.tcol])

        return similar[0]

# http://www.cs.bham.ac.uk/~pxt/IDA/term_selection.pdf
class Entropy(SelectionStrategy):
    def pick(self, documents, feedback=None):
        groups = documents.groupby('document')

        f = lambda x: pd.Series(x.value_counts(normalize=True))
        df = groups[self.tcol].apply(f).reset_index(level=0, drop=True)
        df = df.groupby(df.index).aggregate(st.entropy)

        return df.argmax()
