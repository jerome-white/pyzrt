import functools as ft
import collections as cl
from pathlib import Path

import whoosh.index as wndx
from whoosh.fields import Schema, ID, TEXT
from whoosh.qparser import QueryParser
from whoosh.qparser.syntax import OrGroup
from whoosh.scoring import BM25F
from whoosh.analysis import SimpleAnalyzer

from pyzrt.core.collection import TermCollection
from pyzrt.search.sys import Search

Entry = cl.namedtuple('Entry', 'document, content')

@ft.singledispatch
def WhooshEntry(value):
    raise TypeError('{0} not supported'.format(type(value)))

@WhooshEntry.register(Path)
def _(value):
    identity = lambda x: x
    args = map(str, map(lambda f: f(value), (identity, TermCollection)))

    return Entry(*args)

@WhooshEntry.register(dict)
def _(value):
    return Entry(**{ x: value[x] for x in Entry._fields })

@WhooshEntry.register(str)
def _(value, collect=False):
    document = Path(value)
    content = TermCollection(document) if collect else None

    return Entry(document, content)

@WhooshEntry.register(type(None))
def _(value):
    return Entry(ID(stored=True, unique=True),
                 TEXT(analyzer=SimpleAnalyzer(), phrase=False))

def WhooshSchema():
    entry = WhooshEntry(None)._asdict()

    return Schema(**entry)

# class Entry(_Entry):
#     def __new__(cls, document, contents):
#         return super(Entry, cls).__new__(cls, document, contents)

#     @classmethod
#     def asschema(cls):
#         entry = cls(ID(stored=True, unique=True), TEXT)
#         return Schema(**entry._asdict())

#     def toschema(self):
#         tc = TermCollection
#         return type(self)(*map(str, (document, TermCollection(document))))

class WhooshSearch(Search):
    def __init__(self, index, qrels):
        super().__init__(qrels)

        self.index = wndx.open_dir(index)
        self.session = 0

    def execute(self, query, weighting=None):
        parser = QueryParser('content', self.index.schema, group=OrGroup)
        whquery = parser.parse(str(query))
        session = 'Q{0}'.format(self.session)

        if weighting is None:
            weighting=BM25F()

        with self.index.searcher(weighting=weighting) as searcher:
            results = searcher.search(whquery, limit=self.count)
            for (i, hit) in enumerate(results, 1):
                doc = Path(hit['document'])
                out = [
                    0,         # * qid
                    session,   #   iter
                    doc.stem,  # * docno
                    i,         #   rank
                    hit.score, # * sim
                    'whoosh',  #   run_id
                ]

                yield ' '.join(map(str, out))

        self.session += 1
