import functools as ft
import itertools as it
import collections as cl

import numpy as np
import networkx as nx

from pyzrt.util import zutils
from pyzrt.search.doc import IndriQuery
from pyzrt.retrieval.regionalization import PerRegion, CollectionAtOnce

def Query(terms, model, num, **kwargs):
    return _Query.builder(terms, model, num, **kwargs)

class _Query:
    def __init__(self, doc, num):
        self.doc = doc
        self.num = num
        self.regionalize = None

    def __str__(self):
        query = IndriQuery(self.num)
        query.add(self.compose())

        return str(query)

    def compose(self):
        terms = map(self.make, self.regionalize)
        return ' '.join(map(str, it.chain.from_iterable(terms)))

    def make(self, region):
        raise NotImplementedError()

    @staticmethod
    def builder(terms, model, num, **kwargs):
        return {
            'ua': BagOfWords,
            'sa': Synonym,
            'u1': ft.partial(Synonym, n_longest=1),
            'un': ShortestPath,
            'uaw': TotalWeight,
            'saw': LongestWeight,
        }[model](terms, num, **kwargs)

# ua
class BagOfWords(_Query):
    def __init__(self, doc, num):
        super().__init__(doc, num)
        self.regionalize = CollectionAtOnce(self.doc)

    def make(self, collection):
        yield from collection

# sa, u1
class Synonym(_Query):
    def __init__(self, doc, num, n_longest=None):
        super().__init__(doc, num)
        self.n = n_longest
        self.regionalize = PerRegion(self.doc)

    def make(self, collection):
        collection.bylength()

        iterable = cl.deque([ it.islice(collection, 0, self.n) ])
        if self.n is None or self.n > 1:
            iterable.appendleft([ '#syn(' ])
            iterable.append([ ')' ])

        yield from it.chain.from_iterable(iterable)

class WeightedTerm:
    def __init__(self, term, weight):
        self.term = term
        self.weight = weight

    def __str__(self):
        return '{0} {1}'.format(self.weight, self.term)

class Weighted(_Query):
    def __init__(self, doc, num, alpha):
        super().__init__(doc, num)
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
            yield WeightedTerm(term, weight)

    def make(self, collection):
        operator = '#{0}('.format(self.operator)

        if len(collection) == 1:
            yield collection[0]
        else:
            yield from it.chain([ operator ],
                                self.combine(collection),
                                [ ')' ])

# uaw
class TotalWeight(Weighted):
    def __init__(self, doc, num, alpha=0.5):
        super().__init__(doc, num, alpha)
        self.operator = 'weight'
        self.regionalize = CollectionAtOnce(self.doc)

# saw
class LongestWeight(Weighted):
    def __init__(self, doc, num, alpha=0.5):
        super().__init__(doc, num, alpha)
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

# un
class ShortestPath(_Query):
    def __init__(self, doc, num):
        super().__init__(doc, num)
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
