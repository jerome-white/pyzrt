import sys
import itertools
import operator as op
import xml.etree.ElementTree as et
from pathlib import Path
from functools import singledispatch

from pyzrt.core.collection import TermCollection
from pyzrt.parsing.strainer import _Strainer

def Parser(parser_type, *args):
    return _Parser.builder(parser_type, *args)

class Document:
    def __init__(self, docno, text):
        self.docno = docno
        self.text = text

    def xerox(self, text):
        return type(self)(self.docno, text)

    def __str__(self):
        return self.text

class _Parser():
    def __init__(self, strainer=None):
        self.strainer = _Strainer() if strainer is None else strainer

    def parse(self, document):
        yield from map(self.strainer.strain, self._parse(document))

    def _parse(self, doc):
        raise NotImplementedError()

    @staticmethod
    def builder(parser_type, *args):
        return {
            'pt': PseudoTermParser,
            'wsj': WSJParser,
            'test': TestParser,
            'pass': PassThroughParser,
            'ngram': NGramParser,
        }[parser_type](*args)

class TestParser(_Parser):
    def _parse(self, doc):
        with doc.open() as fp:
            yield Document(doc.name, fp.read())

class WSJParser(_Parser):
    def _parse(self, doc):
        xml = doc.read_text().replace('&', ' ')

        # overcome poorly formed XML (http://stackoverflow.com/a/23891895)
        combos = itertools.chain('<root>', xml, '</root>')
        root = et.fromstringlist(combos)

        for i in root.findall('DOC'):
            docno = i.findall('DOCNO')
            assert(len(docno) == 1)
            docno = docno.pop().text.strip()

            text = []
            for j in ('LP', 'TEXT'):
                for k in i.findall(j):
                    text.append(k.text)
            text = ' '.join(text)

            yield Document(docno, text)

class _TermDocumentParser(_Parser):
    def _parse(self, doc):
        yield Document(doc.stem, self.tostring(TermCollection(doc)))

    def tostring(self, doc):
        raise NotImplementedError()

class PseudoTermParser(_TermDocumentParser):
    def tostring(self, doc):
        return str(doc)

class NGramParser(_TermDocumentParser):
    def tostring(self, doc):
        return doc.tostring(repr)

class PassThroughParser(_Parser):
    def _parse(self, doc):
        yield Document(doc.stem, doc.read_text())
