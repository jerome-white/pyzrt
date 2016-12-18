import itertools
import collections
import operator as op

import numpy as np
import pandas as pd
import networkx as nx

from zrtlib.indri import IndriQuery

class TermDocument:
    def __init__(self, document):
        self.df = pd.read_csv(document)
        self.df.sort_values(by=[ 'start', 'end' ], inplace=True)

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
        yield from map(op.itemgetter(1), groups)

class Query:
    def __init__(self, path):
        self.doc = TermDocument(str(path))

    def __str__(self):
        terms = map(self.regionalize, self.doc.regions())
        query = IndriQuery()
        query.add(' '.join(itertools.chain.from_iterable(terms)))

        return str(query)

class BagOfWords(Query):
    def regionalize(self, region):
        yield from map(op.attrgetter('term'), region.itertuples())

class Synonym(BagOfWords):
    def __init__(self, path, longest=0):
        super().__init__(path)
        self.n = longest

    def regionalize(self, region):
        if self.n > 0:
            df = region.assign(length = lambda x: x.end - x.start)
            df = df.sort_values('length').drop('length', axis=1).tail(self.n)
        else:
            df = region

        yield from itertools.chain(['#syn('], super().regionalize(df), [')'])

class ShortestPath(Query):
    def __init__(self, path, partials=True):
        super().__init__(path)
        self.partials = partials

    def remove_partials(self, region):
        length = region['ngram'].str.len()
        fulls = length == region['end'] - region['start']

        return region[fulls]

    def regionalize(self, region):
        df = region if self.partials else self.remove_partials(region)
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
