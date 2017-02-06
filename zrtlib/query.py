import itertools
import operator as op
from collections import namedtuple

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

from zrtlib.indri import IndriQuery
from zrtlib.document import TermDocument, Region

Node = namedtuple('Node', 'term, offset')
OptimalPath = namedtuple('OptimalPath', 'deviation, path')

def QueryBuilder(model, terms):
    (Model, kwargs) = {
        'ua': (BagOfWords, {}),
        'sa': (Synonym, {}),
        'u1': (Synonym, {
            'n_longest': 1,
        }),
        'un': (ShortestPath, {
            'partials': False,
        }),
        'uaw': (TotalWeight, {}),
        'saw': (LongestWeight, {}),
    }[model]

    return Model(terms, **kwargs)

class Query:
    def __init__(self, doc):
        self.doc = doc
        
    def __str__(self):
        terms = map(self.regionalize, self.doc.regions())
        query = IndriQuery()
        query.add(' '.join(itertools.chain.from_iterable(terms)))

        return str(query)

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

        f = lambda x: Node(x.term, x.start)

        graph = nx.DiGraph()

        for i in range(len(df)):
            source = df.iloc[i]
            u = None
            for j in range(i + 1, len(df)):
                target = df.iloc[j]
                if target.start > source.end:
                    break
                if target.start <= source.start:
                    continue

                if u is None:
                    u = f(source)
                weight = source.end - target.start

                graph.add_edge(u, f(target), weight=weight)

        if len(graph) == 0:
            return source.term
        assert(nx.is_directed_acyclic_graph(graph))

        (source, target) = [ f(df.iloc[x]) for x in (0, -1) ]
        optimal = OptimalPath(np.inf, None)

        for i in nx.all_shortest_paths(graph, source, target, weight='weight'):
            weights = []
            for (u, v) in zip(i, i[1:]):
                d = graph.get_edge_data(u, v)
                weights.append(d['weight'])

            deviation = np.std(weights)
            if deviation < optimal.deviation:
                optimal = OptimalPath(deviation, i)
        assert(optimal.path is not None)

        yield from map(op.attrgetter('term'), optimal.path)
