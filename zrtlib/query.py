import itertools
import functools
import operator as op
from collections import namedtuple

import numpy as np
import graph_tool.all as gt

from zrtlib.indri import IndriQuery
from zrtlib.document import Region

Node_ = namedtuple('Node', 'term, offset')
Node = lambda x: Node_(x.term, x.start)
OptimalPath = namedtuple('OptimalPath', 'deviation, path')

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

        graph = gt.Graph(directed=True)
        nodes = graph.new_vertex_property('object')
        weights = graph.new_edge_property('int')

        for source in df.itertuples():
            u = graph.add_vertex()
            nodes[u] = source
            dest = df[(df.start > source.start) & (df.start <= source.end)]
            for target in dest.itertuples():
                v = graph.add_vertex()
                nodes[v] = target
                edge = graph.add_edge(u, v)
                weights[edge] = source.end - target.start

        if len(graph) == 0:
            return u.term
        # assert(nx.is_directed_acyclic_graph(graph))

        (source, target) = [ nodes[x] for x in (0, -1) ]
        optimal = OptimalPath(np.inf, None)

        for i in gt.all_shortest_paths(graph, source, target, weights):
            path = []
            for (u, v) in zip(i, i[1:]):
                edge = graph.edge(u, v)
                path.append(weights[edge])

            deviation = np.std(path)
            if deviation < optimal.deviation:
                optimal = OptimalPath(deviation, i)

        yield from map(op.attrgetter('term'), optimal.path)
