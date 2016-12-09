import pandas as pd
from collections import namedtuple

QueryID = namedtuple('QueryID', 'topic, number')

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
    def __init__(self, doc):
        self.df = pd.read_csv(doc)
        self.df.sort_values(by=[ 'start', 'end' ], inplace=True)

    def __str__(self):
        return self.df.to_csv(columns=[ 'term' ],
                              header=False,
                              index=False,
                              line_terminator=' ',
                              sep=' ')
