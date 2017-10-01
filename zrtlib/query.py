import itertools
import functools
import operator as op
from collections import namedtuple

import numpy as np
import networkx as nx

# from zrtlib import logger
from zrtlib.indri import IndriQuery
from zrtlib.document import Region

GraphPath = namedtuple('GraphPath', 'path, deviation')

def QueryBuilder(terms, model='ua'):
    return {
        'ua': BagOfWords,
        'sa': Synonym,
        'u1': functools.partial(Synonym, n_longest=1),
        'un': functools.partial(ShortestPath, partials=False),
        'uaw': TotalWeight,
        'saw': LongestWeight,
        'baseline': Standard,
    }[model](terms)

class Query:
    def __init__(self, doc):
        self.doc = doc

    def __str__(self):
        query = IndriQuery()
        query.add(self.compose())

        return str(query)

    def descending(self, docs, limit=None):
        by = [ 'length', 'start', 'end' ]
        df = docs.sort_values(by=by, ascending=False)

        return df if limit is None else df.head(limit)

    def compose(self):
        terms = map(self.regionalize, self.doc.regions())
        return ' '.join(itertools.chain.from_iterable(terms))

    def regionalize(self, region):
        raise NotImplementedError()

class Standard(Query):
    def compose(self):
        return self.doc.regions()

class BagOfWords(Query):
    def regionalize(self, region):
        yield from map(op.attrgetter('term'), region.df.itertuples())

class Synonym(BagOfWords):
    def __init__(self, doc, n_longest=None):
        super().__init__(doc)
        self.n = n_longest

    def regionalize(self, region):
        df = self.descending(region.df, self.n)
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
        return dict(self.discount(self.descending(docs)))

    def combine(self, df, weights, precision=10):
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

        yield from self.combine(region.df, self.weights)

        if region.last:
            yield ')'

class LongestWeight(Weighted):
    def regionalize(self, region):
        weights = self.get_weights(region.df)
        body = self.combine(region.df, weights)

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

        terms = len(df)
        if terms == 0:
            return ''
        elif terms == 1:
            return df.iloc[0]['term']

        graph = nx.DiGraph()

        for source in df.itertuples():
            dest = df[(df.start > source.start) & (df.start <= source.end)]
            for target in dest.itertuples():
                weight = source.end - target.start
                graph.add_edge(source.Index, target.Index, weight=weight)

        # assert(graph.size() > 0)
        # assert(nx.is_directed_acyclic_graph(graph))

        best = None
        (source, target) = df.index[::len(df.index) - 1]
        for i in nx.all_shortest_paths(graph, source, target, weight='weight'):
            weights = []
            for edge in zip(i, i[1:]):
                d = graph.get_edge_data(*edge)
                weights.append(d['weight'])
            deviation = np.std(weights)

            if best is None or deviation < best.deviation:
                best = GraphPath(i, deviation)

        yield from map(lambda x: df.ix[x]['term'], best.path)
