import pandas as pd

class Sieve:
    def like(self, term, documents):
        appearances = self._like(term, documents)
        return documents[documents['document'].isin(appearances)]

    def _like(self, term, documents):
        raise NotImplementedError()

class TermSieve(Sieve):
    def _like(self, term, documents):
        yield from documents[documents['term'] == term]['document']

class ClusterSieve(TermSieve):
    def __init__(self, clusters):
        self.clusters = pd.read_csv(clusters, index_col=False)

    def _like(self, term, documents):
        column = 'value'

        # Documents containing this term...
        appearances = super()._like(term, documents)

        # ... clusters of those documents...
        others = self.clusters[(self.clusters['type'] == 'document') &
                               (self.clusters[column].isin(appearances))]

        # ... documents in those clusters.
        docs = self.clusters[self.clusters['cluster'].isin(others['cluster'])]

        return docs[column]
