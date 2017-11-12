import functools
import operator as op
import itertools as it
from collections import namedtuple

import numpy as np
import networkx as nx

# from zrtlib import logger
from zrtlib.indri import IndriQuery

def QueryBuilder(terms, model='ua'):
    return {
        'ua': BagOfWords,
        'sa': Synonym,
        'u1': functools.partial(Synonym, n_longest=1),
        'un': ShortestPath,
        'uaw': TotalWeight,
        'saw': LongestWeight,
        'baseline': Standard,
    }[model](terms)

class Regionalize:
    def __init__(self, document):
        self.document = document

    def __iter__(self):
        raise NotImplementedError()

class PerRegion(Regionalize):
    def __iter__(self):
        yield from self.document.regions()

class CollectionAtOnce(Regionalize):
    def __iter__(self):
        yield self.document

class Query:
    def __init__(self, doc):
        self.doc = doc
        self.regionalize = None

    def __str__(self):
        query = IndriQuery()
        query.add(self.compose())

        return str(query)

    def compose(self):
        terms = map(self.make, self.regionalize)
        return ' '.join(map(str, it.chain.from_iterable(terms)))

    def make(self, region):
        raise NotImplementedError()

class Standard(Query):
    def compose(self):
        return self.doc.read_text()

class BagOfWords(Query):
    def __init__(self, doc):
        super().__init__(doc)
        self.regionalize = CollectionAtOnce(self.doc)

    def make(self, collection):
        yield from collection

class Synonym(Query):
    def __init__(self, doc, n_longest=None):
        super().__init__(doc)
        self.n = n_longest
        self.regionalize = PerRegion(self.doc)

    def make(self, collection):
        collection.bylength()
        terms = it.islice(collection, 0, self.n)

        yield from it.chain(['#syn('], terms, [')'])

class WeightedTerm:
    def __init__(self, term, weight):
        self.term = term
        self.weight = weight

    def __str__(self):
        return '{0} {1}'.format(self.weight, self.term)

class Weighted(Query):
    def __init__(self, doc, alpha):
        super().__init__(doc)
        self.alpha = alpha
        self.operator = None

    def discount(self, collection):
        previous = []

        for term in collection:
            a = self.alpha * len(term)
            w = a / (1 + a)
            p = np.prod(previous) if previous else 1

            yield (term, w * p)

            previous.append(1 - w)

    def combine(self, region, threshold=1e-4):
        region.bylength()

        for (term, weight) in self.discount(region):
            if weight < threshold:
                break
            yield WeightedTerm(weight, term)

    def make(self, collection):
        operator = '#{0}('.format(self.operator)

        yield from it.chain([operator], self.combine(collection), [')'])

class TotalWeight(Weighted):
    def __init__(self, doc, alpha=0.5):
        super().__init__(doc, alpha)
        self.operator = 'weight'
        self.regionalize = CollectionAtOnce(self.doc)

class LongestWeight(Weighted):
    def __init__(self, doc, alpha=0.5):
        super().__init__(doc, alpha)
        self.operator = 'wsyn'
        self.regionalize = PerRegion(self.doc)

class GraphPath:
    def __init__(self, path, deviation=np.inf):
        self.path = path
        self.deviation = deviation

    def __iter__(self):
        yield from self.path

    def __lt__(self, other):
        return self.deviation < other.deviation

class ShortestPath(Query):
    def __init__(self, doc):
        super().__init__(doc)
        self.regionalize = PerRegion(self.doc)

    def make(self, collection):
        graph = nx.DiGraph()

        for source in collection:
            u = collection.index(source)
            for target in collection.immediates(u):
                v = collection.index(target)
                weight = source.end() - target.end()
                graph.add_edge(u, v, weight=weight)


        (source, target) = (0, len(collection) - 1)
        best = GraphPath([ source ])

        if len(graph):
            for i in nx.all_shortest_paths(graph,
                                           source,
                                           target,
                                           weight='weight'):
                weights = []
                for edge in zip(i, i[1:]):
                    d = graph.get_edge_data(*edge)
                    weights.append(d['weight'])
                current = GraphPath(i, np.std(weights))

                if current < best:
                    best = current

        yield from map(lambda x: collection[x], best)
