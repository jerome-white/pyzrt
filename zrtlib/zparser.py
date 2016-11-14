import sys
import itertools
import xml.etree.ElementTree as et
from pathlib import Path
from functools import singledispatch

from zrtlib import logger

@singledispatch
def normalize(string, lower=True):
    s = ' '.join(string.split())
    return s.lower() if lower else s

@normalize.register(list)
def _(string, lower=True):
    return normalize(' '.join(string), lower)

class Strainer:
    def strain(self, data):
        return normalize(data, False)

class AlphaNumericStrainer(Strainer):
    def __init__(self, extended=False):
        self.table = {}

        for i in range(128):
            c = chr(i)
            self.table[i] = c if c.isalnum() else ' '

        if extended:
            self.table.update({ i: ' ' for i in range(128, 256) })

    def strain(self, data):
        return normalize(data.translate(self.table))

class Parser():
    def __init__(self, strainer=None):
        self.strainer = strainer if strainer else Strainer()

    def parse(self, document):
        try:
            relevant = self.extract(document)
        except et.ParseError as e:
            log = logger.getlogger(True)
            msg = '{0}: line {1} col {2}'
            log.error(msg.format(str(i), *e.position))
            return

        for (docno, text) in map(self.func, relevant):
            yield (docno, self.strainer.strain(text))

    def func(self, path):
        raise NotImplementedError()

    def extract(self, path):
        raise NotImplementedError()

class TestParser(Parser):
    def func(self, doc):
        with doc.open() as fp:
            return (doc.name, fp.read())

    def extract(self, path):
        yield from [ path ]
    
class WSJParser(Parser):
    def func(self, doc):
        docno = doc.findall('DOCNO')
        assert(len(docno) == 1)
        docno = docno.pop().text.strip()

        text = []
        for i in [ 'LP', 'TEXT' ]:
            for j in doc.findall(i):
                text.append(j.text)
        
        return (docno, text)
    
    def extract(self, path):
        xml = path.read_text().replace('&', ' ')

        # overcome poorly formed XML (http://stackoverflow.com/a/23891895)
        combos = itertools.chain('<root>', xml, '</root>')
        root = et.fromstringlist(combos)
        
        yield from root.findall('DOC')
