import sys
import itertools
import xml.etree.ElementTree as et
from pathlib import Path
from functools import singledispatch
from multiprocessing import Pool

from zrtlib import logger

@singledispatch
def normalize(string, lower=True):
    s = ' '.join(string.split())
    return s.lower() if lower else s

@normalize.register(list)
def _(string, lower=True):
    return normalize(' '.join(string), lower)

###########################################################################

class Corpus(dict):
    def __init__(self, path):
        super().__init__()
        
        for i in path.iterdir():
            with i.open() as fp:
                self[i.name] = fp.read()
# http://stackoverflow.com/a/24602374
#     def __init__(self, parser):
#         super().__init__(parser.parse())

###########################################################################

class Strainer:
    def strain(self, data):
        raise NotImplementedError()

class AlphaNumericStrainer(Strainer):
    def __init__(self):
        self.table = {}
        for i in range(2 ** 8):
            c = chr(i)
            self.table[i] = c if c.isalnum() else ' '

    def strain(self, data):
        return normalize(data.translate(self.table))

###########################################################################

class Parser():
    def func(self, doc):
        raise NotImplementedError()

    def extract(self, path):
        raise NotImplementedError()
    
    def parse(self, strainer=None, file_list=sys.stdin):
        log = logger.getlogger(True)
        
        with Pool() as pool:
            for i in file_list:
                path = Path(i.strip())
                log.info(str(path))

                try:
                    relevant = self.extract(path)
                except et.ParseError as e:
                    msg = '{0}: line {1} col {2}'
                    log.error(msg.format(str(path), *e.position))
                    continue

                for (docno, text) in pool.imap_unordered(self.func, relevant):
                    if strainer:
                        text = strainer.strain(text)
                    
                    yield (docno, text)

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
        
        return (docno, normalize(text, False))
    
    def extract(self, path):
        xml = path.read_text().replace('&', ' ')

        # overcome pooly formed XML (http://stackoverflow.com/a/23891895)
        combos = itertools.chain('<root>', xml, '</root>')
        root = et.fromstringlist(combos)
        
        yield from root.findall('DOC')
