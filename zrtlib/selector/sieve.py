import operator as op
import collections

class Sieve:
    def like(self, term, documents):
        raise NotImplementedError()

class TermSieve(Sieve):
    def like(self, term, documents):
        matches = documents[documents['term'] == term]
        docs = matches.groupby('document', sort=False)

        yield from map(op.itemgetter(1), docs)

class ClusterSieve(Sieve):
    def __init__(self, clusters):
        self.clusters = collections.defaultdict(set)
        
        with clusters.open() as fp:
            reader = csv.DictReader(fp)
            for line in reader:
                self.clusters[line['cluster']].add(line['document'])

    def like(self, term, documents):
        matches = documents[documents['term'] == term]
        appearances = matches['document'].unique()

        counts = collections.Counter()
        for (i, docs) in self.clusters.items():
            counts[i] += len(docs.intersection(appearances))

        ((best, _), *_) = c.most_common()
        for i in self.clusters[best]:
            yield documents[documents['document'] == i]
