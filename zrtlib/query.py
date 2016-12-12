import pandas as pd
import operator as op
import itertools
import collections

from zrtlib.indri import IndriQuery

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

class Term:
    def __init__(self, term, start, end):
        self.term = term
        self.start = start
        self.end = end

    def __lt__(self, other):
        return self.end - self.start < other.end - other.start

class TermDocument:
    def __init__(self, doc):
        self.df = pd.read_csv(doc)
        self.df.sort_values(by=[ 'start', 'end' ], inplace=True)

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

class RetainLongest(Retainer):
    def __init__(self, n=None):
        self.n = n

    def _retain(self, terms):
        terms.sort()
        yield from itertools.islice(reversed(terms), 0, self.n)

class Clustered(Query):
    def __init__(self, path, indri_operator, retainer=None):
        super().__init__(path)
        self.operator = indri_operator
        self.retainer = Retainer() if retainer is None else retainer

    def __iter__(self):
        last = None
        terms = []
        f = lambda x: '{0}({1})'.format(self.operator,
                                        ' '.join(self.retainer.retain(x)))

        for i in self.doc:
            if last is not None:
                if i.start > last.end:
                    yield f(terms)
                    terms = []
                else:
                    terms.append(i)
            last = i

        if terms:
            yield f(terms)
