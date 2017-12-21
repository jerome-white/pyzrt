import functools as ft
import collections as cl
from pathlib import Path

import whoosh.index as wndx
from whoosh.fields import Schema, ID, TEXT
from whoosh.qparser import QueryParser

from pyzrt.core.collection import TermCollection
from pyzrt.indri.sys import Search

Entry = cl.namedtuple('_Entry', 'document, content')

@ft.singledispatch
def WhooshEntry(value=None):
    return Entry(ID(stored=True, unique=True), TEXT)

@WhooshEntry.register(Path)
def _(value):
    identity = lambda x: x
    args = map(str, map(lambda x: x(value), (identity, TermCollection)))
    return Entry(*args)

@WhooshEntry.register(dict)
def _(value):
    return Entry(**value)

@WhooshEntry.register(str)
def _(value, collect=False):
    document = Path(value)
    content = TermCollection(document) if collect else None

    return Entry(document, content)

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

    def execute(self, query):
        parser = QueryParser('contents', self.index.schema)
        whquery = parser.parse(str(query))

        with self.index.searcher() as searcher:
            results = searcher.search(whquery, limit=self.count)
            for (i, hit) in enumerate(results):
                doc = Path(hit['doc'])
                out = [
                    0,             # * qid
                    self.session,  #   iter
                    doc.stem,      # * docno
                    i,             #   rank
                    hit.score,     # * sim
                    'whoosh',      #   run_id
                ]

                yield '\t'.join(map(str, out))

        self.session += 1
