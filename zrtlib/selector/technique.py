import pandas as pd
import scipy.stats as st

from zrtlib.document import HiddenDocument

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
        df = (self.
              documents['term'].
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
