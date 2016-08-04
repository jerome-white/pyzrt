import re
import itertools

import logger
from corpus import Document

import multiprocessing as mp
import xml.etree.ElementTree as et

from pathlib import Path

class Parser():
    def f(self, doc):
        raise NotImplementedError

    def paths(self):
        raise NotImplementedError

    def extract(self):
        raise NotImplementedError
    
    def parse(self):
        log = logger.getlogger(True)
        
        with mp.Pool() as pool:
            for path in self.paths():
                log.info(str(path))

                try:
                    relevant = self.extract(path)
                except et.ParseError as e:
                    msg = '{0}: line {1} col {2}'
                    log.error(msg.format(str(path), *e.position))
                    continue
                    
                for (docno, data) in pool.imap_unordered(self.f, relevant):
                    yield (docno, Document(path, data))

class WSJParser(Parser):
    def f(self, doc):
        docno = doc.findall('DOCNO')
        assert(len(docno) == 1)
        docno = docno.pop().text.strip()

        text = []
        for i in [ 'LP', 'TEXT' ]:
            for j in doc.findall(i):
                text.append(j.text)
        text = ' '.join(' '.join(text).split()).lower()
        
        return (docno, text)

    def paths(self):
        p = Path('WSJ')
        
        yield from p.glob('*/WSJ_*')
    
    def extract(self, path):
        # http://stackoverflow.com/a/23891895            
        xml = re.sub('&', ' ', path.read_text())
        combos = itertools.chain('<root>', xml, '</root>')
        root = et.fromstringlist(combos)
        
        yield from root.findall('DOC')
