import re
import pickle
import itertools

import logger
import distance
import similarity
from corpus import Corpus, Document

import operator as op
import multiprocessing as mp
import xml.etree.ElementTree as et

from pathlib import Path
from collections import OrderedDict

def wsj(doc):
    docno = doc.findall('DOCNO')
    assert(len(docno) == 1)
    docno = docno.pop().text.strip()

    text = []
    for i in [ 'LP', 'TEXT' ]:
        for j in doc.findall(i):
            text.append(j.text)
    text = ' '.join(' '.join(text).split()).lower()
            
    return (docno, text)

log = logger.getlogger(True)

corpus_pickle = 'corpus_1990-1992.pkl'
corpus = pickle.load(open(corpus_pickle, 'rb'))
# corpus = Corpus()

if not corpus:
    with mp.Pool() as pool:
        path = Path('WSJ')
        for fpath in path.glob('*/WSJ_*'):
            log.info(str(fpath))
            
            # http://stackoverflow.com/a/23891895            
            xml = re.sub('&', ' ', fpath.read_text())
            combos = itertools.chain('<root>', xml, '</root>')
            
            try:
                root = et.fromstringlist(combos)
            except et.ParseError as e:
                msg = '{0}: line {1} col {2}'
                log.error(msg.format(str(fpath), *e.position))
                continue
            
            for (docno, data) in pool.imap_unordered(wsj, root.findall('DOC')):
                corpus[docno] = Document(fpath, data)
    pickle.dump(corpus, open(corpus_pickle, 'wb'))
    
for i in [ 'documents', 'characters' ]:
    f = getattr(corpus, i)
    log.info('{0}: {1}'.format(i, f()))

matrix = similarity.similarity(corpus.mend(corpus.fragment()))
pickle.dump(matrix, open('wsj-matrix.pkl', 'wb'))

dots = similarity.to_numpy(matrix)
similarity.dotplot(dots, 'wsj.png')
