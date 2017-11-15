import sys
import itertools
import xml.etree.ElementTree as et
from pathlib import Path
from functools import singledispatch

from zrtlib import logger
from zrtlib.strainer import Strainer
# from zrtlib.document import TermDocument
from zrtlib.terms import TermCollection

class Document:
    def __init__(self, docno, text):
        self.docno = docno
        self.text = text

class Parser():
    def __init__(self, strainer=None):
        self.strainer = Strainer() if strainer is None else strainer

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

class TestParser(Parser):
    def _parse(self, doc):
        with doc.open() as fp:
            yield Document(doc.name, fp.read())

class WSJParser(Parser):
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

class TermDocumentParser(Parser):
    def __init__(self, tostring, strainer=None):
        super().__init__(strainer)
        self.tostring = tostring

    def _parse(self, doc):
        text = ' '.join(map(self.tostring, TermCollection(doc)))
        yield Document(doc.stem, text)

    def tostring(self, term):
        raise NotImplementedError()

class PseudoTermParser(TermDocumentParser):
    def __init__(self, strainer=None):
        super().__init__(str, strainer)

class NGramParser(TermDocumentParser):
    def __init__(self, strainer=None):
        super().__init__(repr, strainer)

class PassThroughParser(Parser):
    def _parse(self, doc):
        yield Document(doc.stem, doc.read_text())
