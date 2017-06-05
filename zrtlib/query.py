import itertools
import functools
import operator as op
from collections import namedtuple

import numpy as np
import igraph as ig

# from zrtlib import logger
from zrtlib.indri import IndriQuery
from zrtlib.document import Region

GraphPath = namedtuple('GraphPath', 'path, weight, variance')

class Node:
    def __init__(self, node):
        self.term = node.term
        self.offset = node.start

    def __hash__(self):
        return hash((self.term, self.offset))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.term == other.term and self.offset == other.offset

def QueryBuilder(terms, model='ua'):
    return {
        'ua': BagOfWords,
        'sa': Synonym,
        'u1': functools.partial(Synonym, n_longest=1),
        'un': functools.partial(ShortestPath, partials=False),
        'uaw': TotalWeight,
        'saw': LongestWeight,
    }[model](terms)

class Query:
    def __init__(self, doc):
        self.doc = doc

    def __str__(self):
        query = IndriQuery()
        query.add(self.compose())

        return str(query)

    @staticmethod
    def descending(docs, limit=None):
        by = [ 'length', 'start', 'end' ]
        df = docs.sort_values(by=by, ascending=False)

        return df if limit is None else df.head(limit)

    def compose(self):
        terms = map(self.regionalize, self.doc.regions())
        return ' '.join(itertools.chain.from_iterable(terms))

    def regionalize(self, region):
        raise NotImplementedError()

class BagOfWords(Query):
    def regionalize(self, region):
        yield from map(op.attrgetter('term'), region.df.itertuples())

class Synonym(BagOfWords):
    def __init__(self, doc, n_longest=None):
        super().__init__(doc)
        self.n = n_longest

    def regionalize(self, region):
        df = Query.descending(region.df, self.n)
        r = Region(*region[:3], df)

        yield from itertools.chain(['#syn('], super().regionalize(r), [')'])

class Weighted(Query):
    def __init__(self, doc, alpha=0.5):
        super().__init__(doc)
        self.alpha = alpha

    def discount(self, df):
        previous = []

        for row in df.itertuples():
            a = self.alpha * row.length
            w = a / (1 + a)
            p = np.prod(previous) if previous else 1

            yield (row.Index, w * p)
            
            previous.append(1 - w)

    def get_weights(self, docs):
        return dict(self.discount(Query.descending(docs)))

    @staticmethod
    def combine(df, weights, precision=10):
        for row in df.itertuples():
            if row.Index in weights:
                kg = '{1:.{0}f}'.format(precision, weights[row.Index])
                if float(kg) != 0:
                    yield kg + ' ' + row.term

class TotalWeight(Weighted):
    def __init__(self, doc, alpha=0.5):
        super().__init__(doc, alpha)

        self.weights = self.get_weights(self.doc.df)

    def regionalize(self, region):
        if region.first:
            yield '#weight('

        yield from Weighted.combine(region.df, self.weights)

        if region.last:
            yield ')'

class LongestWeight(Weighted):
    def regionalize(self, region):
        weights = self.get_weights(region.df)
        body = Weighted.combine(region.df, weights)

        yield from itertools.chain(['#wsyn('], body, [')'])

class ShortestPath(Query):
    def __init__(self, doc, partials=True):
        super().__init__(doc)
        self.partials = partials

    def regionalize(self, region):
        df = region.df
        if not self.partials:
            condition = df['ngram'].str.len() == df['length']
            df = df[condition]
            if len(df) == 0:
                return ''

        graph = ig.Graph(n=len(df), directed=True)

        for source in df.itertuples():
            u = df.index.get_loc(source.Index)
            dest = df[(df.start > source.start) & (df.start <= source.end)]
            for target in dest.itertuples():
                v = df.index.get_loc(target.Index)
                w = source.end - target.start

                graph.add_edge(u, v, weight=w)

        if graph.ecount() > 0:
            best = None
            for path in graph.get_all_shortest_paths(0, graph.vcount() - 1):
                weights = []
                for (u, v) in zip(path, path[1:]):
                    edge = graph.es.select(_source=u, _target=v)
                    w = edge['weight'][0] # XXX why is this a list?
                    weights.append(w)
                properties = [ f(weights) for f in (np.sum, np.std) ]

                current = GraphPath(path, *properties)

                if best is None:
                    best = current
                else:
                    if current.weight < best.weight:
                        best = current
                    elif current.weight == best.weight:
                        if current.variance < best.variance:
                            best = current
            indices = best.path
        else:
            indices = [0]

        for i in indices:
            row = df.iloc[i]
            yield row['term']
