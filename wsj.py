import re
import logger
import pickle
import document
import itertools

import xml.etree.ElementTree as et

from pathlib import Path
from multiprocessing import Pool

from segment import Slicer as segmenter
from distance import SequenceDistance as distance

def wsj(doc):
    docno = doc.findall('DOCNO')
    assert(len(docno) == 1)
    docno = docno.pop().text.strip()

    # log.info(docno)

    text = []
    for i in [ 'LP', 'TEXT' ]:
        for j in doc.findall(i):
            text.append(j.text)
    text = ' '.join(' '.join(text).split()).lower()
            
    return (docno, text)

log = logger.getlogger(True)
corpus = document.Corpus()

with Pool() as pool:
    root = Path('/Users/jerome/Documents/Data/corpus/WSJ')
    for fpath in root.glob('*/WSJ_*'):
        log.info(str(fpath))
        
        xml = re.sub('&', ' ', fpath.read_text())
        
        # http://stackoverflow.com/a/23891895
        combos = itertools.chain('<root>', xml, '</root>')
        
        try:
            root = et.fromstringlist(combos)
            for (i, j) in pool.imap_unordered(wsj, root.findall('DOC')):
                d = document.Document(i, fpath, j)
                corpus.append(d)
        except et.ParseError as e:
            log.error('{0}: line {1} col {2}'.format(str(fpath), *e.position))
            
    log.info('Corpus: {0}'.format(len(corpus)))
    # pickle.dump(corpus, open('corpus_90-92.pkl', 'wb'))
    
log.info('similarity')
s = corpus.similarity(segmenter(1000), distance())

log.info('plot')
corpus.dotplot(s, 'wsj.png')
