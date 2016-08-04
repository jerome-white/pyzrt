import re
import pickle
import itertools

import logger
import distance
import similarity
from parser import WSJParser
from corpus import Corpus, Document

import operator as op
import multiprocessing as mp
import xml.etree.ElementTree as et

from pathlib import Path
from collections import OrderedDict

log = logger.getlogger(True)

corpus_pickle = 'corpus_1990-1992.pkl'
# corpus = pickle.load(open(corpus_pickle, 'rb'))

parser = WSJParser()
corpus = Corpus(parser.parse())
pickle.dump(corpus, open(corpus_pickle, 'wb'))

for i in [ 'documents', 'characters' ]:
    f = getattr(corpus, i)
    log.info('{0}: {1}'.format(i, f()))

matrix = similarity.similarity(corpus.mend(corpus.fragment()))
pickle.dump(matrix, open('wsj-matrix.pkl', 'wb'))

dots = similarity.to_numpy(matrix)
similarity.dotplot(dots, 'wsj.png')
