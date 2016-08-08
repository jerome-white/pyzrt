import re
import pickle
import itertools

from pathlib import Path
from operator import itemgetter
from argparse import ArgumentParser

import logger
import distance
from parser import WSJParser
from corpus import Corpus, Document
from similarity import RowPerCPU as Similarity

log = logger.getlogger(True)

arguments = ArgumentParser()
arguments.add_argument('--input-directory')
arguments.add_argument('--output-directory')
arguments.add_argument('--to-pickle')
arguments.add_argument('--from-pickle')
args = arguments.parse_args()

if args.from_pickle:
    with open(args.from_pickle, 'rb') as fp:
        corpus = pickle.load(fp)
else:
    parser = WSJParser()
    documents = parser.parse(args.input_directory)
    corpus = Corpus(sorted(documents, key=itemgetter(0)))
    
if args.to_pickle:
    with open(args.from_pickle, 'wb') as fp:
        pickle.dump(corpus, fp)

for i in [ 'documents', 'characters' ]:
    f = getattr(corpus, i)
    log.info('{0}: {1}'.format(i, f()))
output = Path(args.output_directory)

fragments = FragmentedCorpus(corpus)
log.info('Fragments {0}'.format(len(fragments)))
matrix = Similarity(fragments.strings())

o = output.joinpath('wsj-matrix').with_suffix('.pkl')
with o.open('wb') as fp:
    pickle.dump(matrix, fp)

o = output.joinpath('wsj').with_suffix('.png')
matrix.dotplot(str(o))
