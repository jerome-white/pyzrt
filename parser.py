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

    def extract(self, path):
        raise NotImplementedError
    
    def parse(self, top_level, glob_expression):
        log = logger.getlogger(True)
        path = Path(top_level)
        
        with mp.Pool() as pool:
            for i in path.glob(glob_expression):
                log.info(str(i))

                try:
                    relevant = self.extract(i)
                except et.ParseError as e:
                    msg = '{0}: line {1} col {2}'
                    log.error(msg.format(str(i), *e.position))
                    continue
                    
                for (docno, data) in pool.imap_unordered(self.f, relevant):
                    document = Document(Path(i), data)
                    yield (docno, document)

class WSJParser(Parser):
    def parse(self, top_level, glob_expression='*/WSJ_*'):
        return super().parse(top_level, glob_expression)
        
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
    
    def extract(self, path):
        xml = re.sub('&', ' ', path.read_text())
        # overcome pooly formed XML (http://stackoverflow.com/a/23891895)
        combos = itertools.chain('<root>', xml, '</root>')
        root = et.fromstringlist(combos)
        
        yield from root.findall('DOC')
