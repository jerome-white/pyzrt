import re
import sys
import itertools
import xml.etree.ElementTree as et
from pathlib import Path
from functools import singledispatch
from multiprocessing import Pool

from zrtlib import logger

# # http://stackoverflow.com/a/24602374
# class Corpus(dict):
#     def __init__(self, path):
#         for i in path.iterdir():
#             with i.open() as fp:
#                 self[i.name] = fp.read()

#     def __init__(self, parser):
#         super().__init__(parser.parse())

class Parser():
    def func(self, doc):
        raise NotImplementedError()

    def extract(self, path):
        raise NotImplementedError()
    
    def parse(self, file_list=sys.stdin):
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
                    
                yield from pool.imap_unordered(self.func, relevant)

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
        text = ' '.join(' '.join(text).split()).lower()
        
        return (docno, text)
    
    def extract(self, path):
        xml = re.sub('&', ' ', path.read_text())
        # overcome pooly formed XML (http://stackoverflow.com/a/23891895)
        combos = itertools.chain('<root>', xml, '</root>')
        root = et.fromstringlist(combos)
        
        yield from root.findall('DOC')
