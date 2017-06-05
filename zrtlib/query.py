import itertools
import functools
import operator as op
from collections import namedtuple

import numpy as np
import igraph as ig

from zrtlib.indri import IndriQuery
from zrtlib.document import Region

GraphPath = namedtuple('GraphPath', 'edges, weight, variance')

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

    def compose(self):
        terms = map(self.regionalize, self.doc.regions())

        return ' '.join(itertools.chain.from_iterable(terms))

    def regionalize(self, region):
        raise NotImplementedError()

class BagOfWords(Query):
    def regionalize(self, region):
        yield from map(op.attrgetter('term'), region.df.itertuples())

class Synonym(BagOfWords):
    def __init__(self, path, n_longest=None):
        super().__init__(path)
        self.n = n_longest

    def regionalize(self, region):
        n = len(region.df) if self.n is None else self.n
        df = region.df.nlargest(n, 'length')
        r = Region(*region[:3], df)

        yield from itertools.chain(['#syn('], super().regionalize(r), [')'])

class Weighted(Query):
    def __init__(self, path, alpha=0.5):
        super().__init__(path)
        self.alpha = alpha

    def regionalize(self, region):
        raise NotImplementedError()

    def discount(self, df):
        previous = []

        for row in df.itertuples():
            w = self.alpha * (row.end - row.start)
            i = w / (1 + w)
            j = np.prod(previous) if previous else 1

            yield (row.Index, i * j)

            previous.append(1 - i)

    def combine(self, df, weights):
        for row in df.itertuples():
            if row.Index in weights:
                yield '{0:.10f} {1}'.format(weights[row.Index], row.term)

class TotalWeight(Weighted):
    def __init__(self, path, alpha=0.5):
        super().__init__(path, alpha)

        by = [ 'length', 'start', 'end' ]
        df = self.doc.df.sort_values(by=by, ascending=False)
        self.computed = dict(self.discount(df))

    def regionalize(self, region):
        if region.first:
            yield '#weight('

        yield from self.combine(region.df, self.computed)

        if region.last:
            yield ')'

class LongestWeight(Weighted):
    def regionalize(self, region):
        df = region.df.nlargest(len(region.df), 'length')
        weights = dict(self.discount(df))
        body = super().combine(df, weights)

        yield from itertools.chain(['#wsyn('], body, [')'])

class ShortestPath(Query):
    def __init__(self, path, partials=True):
        super().__init__(path)
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
            for path in g.get_all_shortest_paths(0, g.vcount() - 1):
                weights = []
                for (u, v) in zip(path, path[1:]):
                    edge = g.es.select(_source=u, _target=v)
                    weights.append(edge['weight'][0])
                properties = [ f(weights) for f in (np.sum, np.std) ]

                current = GraphPath(path, *properties)
                if best is None:
                    best = current
                else:
                    if current.length < best.length:
                        best = current
                    elif current.length == best.length:
                        if current.variance < best.variance:
                            best = current
            indices = best.path
        else:
            indices = [0]

        for i in indices:
            row = df.iloc[i]
            yield row['term']
