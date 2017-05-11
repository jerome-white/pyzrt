import operator as op

import numpy as np
import pandas as pd
import scipy.stats as st
from sklearn.feature_extraction.text import TfidfVectorizer

from zrtlib.document import HiddenDocument

class SelectionTechnique:
    def __init__(self):
        self.documents = iter(())

    def __next__(self):
        return next(self.documents)

class Random(SelectionTechnique):
    def __init__(self, documents, weighted=False, seed=None):
        super().__init__()

        weights = 'term' if weighted else None
        df = (documents['term'].
              value_counts().
              sample(frac=1, weights=weights, random_state=seed))

        self.documents = map(op.itemgetter(0), df.iteritems())

class DocumentFrequency(SelectionTechnique):
    def __init__(self, documents):
        super().__init__()

        groups = documents.groupby('document', sort=False)
        df = (groups['term'].
              apply(lambda x: pd.Series(x.unique())).
              value_counts())

        self.documents = map(op.itemgetter(0), df.iteritems())

class TermFrequency(SelectionTechnique):
    def __init__(self, documents):
        super().__init__()

        df = documents['term'].value_counts()

        self.documents = map(op.itemgetter(0), df.iteritems())

# http://www.cs.bham.ac.uk/~pxt/IDA/term_selection.pdf
class Entropy(SelectionTechnique):
    def __init__(self, documents):
        super().__init__()

        groups = documents.groupby('document', sort=False)

        f = lambda x: pd.Series(x.value_counts(normalize=True))
        df = groups['term'].apply(f).reset_index(level=0, drop=True)
        df = (df.
              groupby(df.index, sort=False).
              aggregate(st.entropy).
              sort_values(ascending=False))

        self.documents = map(op.itemgetter(0), df.iteritems())

class Relevance(SelectionTechnique):
    def __init__(self, documents, query, relevant, technique=None):
        super().__init__()

        df = documents[documents['document'].isin(relevant)]
        query = query.df[HiddenDocument.columns['visible']]
        df = df[df['term'].isin(query)]

        if not df.empty:
            if technique is None:
                self.documents = iter(df['term'].unique())
            else:
                self.documents = technique(df)

class TFIDF(SelectionTechnique):
    def __init__(self, documents):
        self.indices = []

        docs = documents.groupby('document', sort=False)
        X = TfidfVectorizer().fit_transform(map(self.terms, docs))

        ordered = np.max(X, axis=1)
        ascending = np.argsort(ordered.toarray(), axis=0)
        descending = np.flipud(ascending.squeeze())

        self.documents = self.stitch(descending)

    # This might be redundant, but it ensures that the order in which
    # TfidfVectorizer sees the documents is the same order that is
    # mapped in the final stitching.
    def terms(self, row):
        (doc, data) = row
        self.indices.append(doc)

        return ' '.join(data.values)

    def stitch(self, indices):
        for i in indices:
            yield self.indices[i]
