import sys
import itertools
import xml.etree.ElementTree as et
from pathlib import Path
from functools import singledispatch

from zrtlib import logger
from zrtlib.strainer import Strainer
from zrtlib.document import TermDocument

@singledispatch
def normalize(string, fmt=None):
    s = ' '.join(string.split())
    return s if fmt is None else fmt(s)

@normalize.register(list)
def _(string, fmt=None):
    return normalize(' '.join(string), fmt)

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
            for j in [ 'LP', 'TEXT' ]:
                for k in i.findall(j):
                    text.append(k.text)
            text = normalize(text, self.strainer.fmt)

            yield Document(docno, text)

class PseudoTermParser(Parser):
    def _parse(self, doc):
        document = TermDocument(doc, False)

        yield Document(doc.stem, str(document))
