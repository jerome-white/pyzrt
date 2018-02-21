import functools as ft
import itertools as it

import numpy as np
import networkx as nx

from pyzrt.util import zutils
from pyzrt.indri.doc import IndriQuery
from pyzrt.retrieval.regionalization import PerRegion, CollectionAtOnce

def Query(terms, model='ua', **kwargs):
    return _Query.builder(terms, model, **kwargs)

class ReprStr:
    def __init__(self, word):
        self.word = word

    def __repr__(self):
        return str(self.word)

class _Query:
    def __init__(self, doc):
        self.doc = doc
        self.regionalize = None

    def __str__(self):
        query = IndriQuery()
        query.add(self.compose())

        return str(query)

    def compose(self):
        terms = map(self.make, self.regionalize)
        return ' '.join(map(repr, it.chain.from_iterable(terms)))

    def make(self, region):
        raise NotImplementedError()

    @staticmethod
    def builder(terms, model, **kwargs):
        return {
            'ua': BagOfWords,
            'sa': Synonym,
            'u1': ft.partial(Synonym, n_longest=1),
            'un': ShortestPath,
            'uaw': TotalWeight,
            'saw': LongestWeight,
        }[model](terms, **kwargs)

class BagOfWords(_Query):
    def __init__(self, doc):
        super().__init__(doc)
        self.regionalize = CollectionAtOnce(self.doc)

    def make(self, collection):
        yield from collection

class Synonym(_Query):
    def __init__(self, doc, n_longest=None):
        super().__init__(doc)
        self.n = n_longest
        self.regionalize = PerRegion(self.doc)

    def make(self, collection):
        collection.bylength()

        iterable = [ it.islice(collection, 0, self.n) ]
        if self.n is None or self.n > 1:
            iterable.insert(0, [ ReprStr('#syn(') ])
            iterable.append([ ReprStr(')') ])

        yield from it.chain.from_iterable(iterable)

class WeightedTerm:
    def __init__(self, term, weight):
        self.term = term
        self.weight = weight

    def __str__(self):
        return '{0} {1}'.format(self.weight, self.term)

class Weighted(_Query):
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

        yield from it.chain([ ReprStr(operator) ],
                            self.combine(collection),
                            [ ReprStr(')') ])

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
    def __init__(self, path=None, deviation=np.inf):
        self.path = [ 0 ] if path is None else path
        self.deviation = deviation

    def __iter__(self):
        yield from self.path

    def __lt__(self, other):
        return self.deviation < other.deviation

class ShortestPath(_Query):
    def __init__(self, doc):
        super().__init__(doc)
        self.regionalize = PerRegion(self.doc)

    def make(self, collection):
        graph = nx.DiGraph()

        for (u, src) in enumerate(collection):
            for v in range(u + 1, len(collection)):
                dst = collection[v]
                weight = src.span - dst.position
                if weight < 0:
                    break
                graph.add_edge(u, v, weight=weight)

        best = GraphPath()

        if len(graph):
            nodes = map(lambda x: x(graph.nodes()), (min, max))
            for i in nx.all_shortest_paths(graph, *nodes, weight='weight'):
                weights = []
                for edge in zutils.pairwise(i):
                    d = graph.get_edge_data(*edge)
                    weights.append(d['weight'])
                current = GraphPath(i, np.std(weights))

                if current < best:
                    best = current

        yield from [ collection[x] for x in best ]
