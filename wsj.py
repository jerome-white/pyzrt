import re
import logger
import pickle
import itertools

import segment
import distance
import similarity

import xml.etree.ElementTree as et

from pathlib import Path
from collections import OrderedDict
from multiprocessing import Pool

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

# corpus = pickle.load(open('corpus_90-92.pkl', 'rb'))
corpus = OrderedDict()

with Pool() as pool:
    root = Path('/Users/jerome/Documents/Data/corpus/WSJ')
    for fpath in root.glob('*/WSJ_*'):
        log.info(str(fpath))
        
        xml = re.sub('&', ' ', fpath.read_text())
        
        # http://stackoverflow.com/a/23891895
        combos = itertools.chain('<root>', xml, '</root>')
        
        try:
            root = et.fromstringlist(combos)
            for (docno, data) in pool.imap_unordered(wsj, root.findall('DOC')):
                corpus[docno] = segment.Document(fpath, data)
        except et.ParseError as e:
            log.error('{0}: line {1} col {2}'.format(str(fpath), *e.position))
            
    log.info('Corpus: {0}'.format(len(corpus)))
    # pickle.dump(corpus, open('corpus_90-92.pkl', 'wb'))

segmentation = segment.segment(corpus, 100)
chunks = similarity.chunk(corpus, segmentation, distance.SequenceDistance)
matrix = similarity.similarity(chunks)
dots = similarity.to_numpy(matrix)
similarity.dotplot(dots, 'wsj.png')
