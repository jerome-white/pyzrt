import operator as op
import collections

class Sieve:
    def like(self, term, documents):
        appearances = self.like_(term, documents)
        return documents[documents['document'].isin(appearances)]

    def like_(self, term, documents):
        raise NotImplementedError()

class TermSieve(Sieve):
    def like_(self, term, documents):
        yield from documents[documents['term'] == term]['document']

class ClusterSieve(TermSieve):
    def __init__(self, clusters, sample=None):
        self.clusters = pd.read_csv(clusters, index_col=False)
        self.sample = sample

    def like_(self, term, documents):
        relevant = super().like_(term, documents)
        column = 'value'
        docs = self.clusters[self.clusters['type'] == 'document' &
                             self.clusters[column].isin(relevant)]

        for (_, group) in docs.groupby('cluster', sort=False):
            df = group[column]
            if self.sample is not None:
                df = df.sample(self.sample)
            yield df
