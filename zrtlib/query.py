import pandas as pd
import operator as op
import itertools
import collections

import numpy as np
import networkx as nx

from zrtlib.indri import IndriQuery

Term = collections.namedtuple('Term', 'term, start, end')
QueryID = collections.namedtuple('QueryID', 'topic, number')

class QueryDoc:
    separator = '-'
    prefix = 'WSJQ00'

    def __init__(self, path):
        self.name = path.stem.zfill(3)
        self.docs = []

    def __iter__(self):
        yield from map(lambda x: et.tostring(x, encoding='unicode'), self.docs)

    def __bool__(self):
        return len(self.docs) > 0

    @classmethod
    def isquery(cls, doc):
        return doc.stem[:len(cls.prefix)] == cls.prefix

    @classmethod
    def components(cls, doc):
        if not cls.isquery(doc):
            raise ValueError()

        (name, number) = doc.stem.split('-')
        topic = name[len(QueryDoc.prefix):]

        return QueryID(topic, number)

    def add(self, query):
        docno = '{0}{1}{2}{3:04d}'.format(QueryDoc.prefix,
                                          self.name,
                                          QueryDoc.separator,
                                          len(self.docs))

        doc = et.Element('DOC')
        et.SubElement(doc, 'DOCNO').text = docno
        et.SubElement(doc, 'TEXT').text = ' '.join(query)

        self.docs.append(doc)

class TermDocument:
    def __init__(self, doc, drop_partial=False):
        self.df = pd.read_csv(doc)
        self.df.sort_values(by=[ 'start', 'end' ], inplace=True)

        if drop_partial:
            length = self.df['ngram'].str.len()
            fulls = length == self.df['end'] - self.df['start']
            self.df = self.df[fulls]

    def __str__(self):
        return self.df.to_csv(columns=[ 'term' ],
                              header=False,
                              index=False,
                              line_terminator=' ',
                              sep=' ')

    def __iter__(self):
        for row in self.df.itertuples():
            yield Term(row.term, row.start, row.end)

class Query:
    def __init__(self, path):
        self.doc = TermDocument(str(path))

    def __str__(self):
        query = IndriQuery()
        query.add(' '.join(list(self)))

        return str(query)

class BagOfWords(Query):
    def __iter__(self):
        for i in self.doc:
            yield i.term

class Retainer:
    def retain(self, terms):
        yield from map(op.attrgetter('term'), self._retain(terms))

    def _retain(self, terms):
        yield from terms

class RetainPath(Retainer):
    def _retain(self, terms):
        graph = nx.DiGraph()

        for (u, v) in itertools.combinations(terms, 2):
            if u.end >= v.start and u.start != v.start:
                weight = u.end - v.start
                graph.add_edge(u, v, weight=weight)

        paths = {}
        (source, target) = [ terms[x] for x in (0, -1) ]
        for i in nx.all_shortest_paths(graph, source, target, weight='weight'):
            weights = []
            for (u, v) in zip(i, i[1:]):
                d = graph.get_edge_data(u, v)
                weights.append(d['weight'])
            key = np.std(weights)
            paths[key] = i
        best = min(paths.keys())

        yield from paths[best]

class RetainLongest(Retainer):
    def __init__(self, n=None):
        self.n = n

    def _retain(self, terms):
        yield from itertools.islice(reversed(terms), 0, self.n)

class Clustered(Query):
    def __init__(self, path, indri_operator=None, retainer=None):
        super().__init__(path)

        if indri_operator is None:
            self.operator = '{0}'
        else:
            self.operator = '#{0}({{0}})'.format(indri_operator)

        self.retainer = Retainer() if retainer is None else retainer

    def tostring(self, terms):
        return self.operator.format(' '.join(self.retainer.retain(terms)))

    def __iter__(self):
        last = None
        terms = []

        for i in self.doc:
            if last is not None:
                if i.start > last.end:
                    yield self.tostring(terms)
                    terms = []
                else:
                    terms.append(i)
            last = i

        if terms:
            yield self.tostring(terms)
