import itertools
import collections
import operator as op

import numpy as np
import pandas as pd
import networkx as nx

from zrtlib.indri import IndriQuery

Region = collections.namedtuple('Region', 'n, first, last, df')

class TermDocument:
    def __init__(self, document, lengths=False):
        self.df = pd.read_csv(document)
        self.df.sort_values(by=[ 'start', 'end' ], inplace=True)

        if lengths:
            self.df['length'] = self.df['end'] - self.df['start']

        self.region_column = 'region'
        region = 0
        updates = {}
        last = None

        self.df[self.region_column] = region
        for row in self.df.itertuples():
            if last is not None:
                region += row.start > last.end
                updates[row.Index] = region
            last = row
        groups = pd.DataFrame(list(updates.values()),
                              index=updates.keys(),
                              columns=[ self.region_column ])
        self.df.update(groups)

    def __str__(self):
        return self.df.to_csv(columns=[ 'term' ],
                              header=False,
                              index=False,
                              line_terminator=' ',
                              sep=' ')
        
    def regions(self):
        groups = self.df.groupby(by=[self.region_column], sort=False)
        n = groups.size().count() - 1

        for (i, (j, df)) in enumerate(groups):
            yield Region(j, i == 0, i == n, df)

class Query:
    def __init__(self, path):
        self.doc = TermDocument(str(path), True)
        
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

        yield from itertools.chain(['#syn('], super().regionalize(df), [')'])

class Weighted(Query):
    def __init__(self, path, alpha=0.5):
        super().__init__(path)
        self.alpha = alpha

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

        graph = nx.DiGraph()

        for i in range(len(df)):
            u = df.iloc[i]
            for j in range(i + 1, len(df)):
                v = df.iloc[j]
                if v.start > u.end:
                    break
                if u.start != v.start:
                    weight = u.end - v.start
                    graph.add_edge(u.term, v.term, weight=weight)

        paths = {}
        (source, target) = [ df.iloc[x].term for x in (0, -1) ]

        for i in nx.all_shortest_paths(graph, source, target, weight='weight'):
            weights = []
            for (u, v) in zip(i, i[1:]):
                d = graph.get_edge_data(u, v)
                weights.append(d['weight'])
            key = np.std(weights)
            paths[key] = i

        yield from paths[min(paths.keys())]
