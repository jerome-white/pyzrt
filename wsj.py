import re
import document
import itertools

import xml.etree.ElementTree as et

from lib import logger
from pathlib import Path
from multiprocessing import Pool

def wsj(fpath):
    log = logger.getlogger()
    log.info(str(fpath))

    xml = re.sub('&', ' ', fpath.read_text())
    # http://stackoverflow.com/a/23891895
    combos = itertools.chain('<root>', xml, '</root>')
    try:
        root = et.fromstringlist(combos)
    except et.ParseError as e:
        log.error('{0}: line {1} col {2}'.format(str(fpath), *e.position))
        return None
    
    for doc in root.findall('DOC'):
        docno = doc.findall('DOCNO')
        assert(len(docno) == 1)
        docno = docno.pop().text.strip()

        text = []
        for i in [ 'LP', 'TEXT' ]:
            for j in doc.findall(i):
                text.append(j.text)
        text = ' '.join(' '.join(text).split()).lower()
            
        yield document.Document(docno, fpath, text)

log = logger.getlogger(True)
log.info('Parse corpus')

with Pool(4, maxtasksperchild=1) as pool:
    root = Path('/Users/jerome/Documents/Data/corpus/WSJ')
    corpus = document.Corpus()
    for i in pool.imap_unordered(wsj, root.glob('*/WSJ_*')):
        if i:
            corpus.append(i)

log.info('similarity')
s = corpus.similarity()
log.info('plot')
corpus.dotplot(s, 'wsj.png')
