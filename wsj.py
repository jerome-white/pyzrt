import pickle
import itertools

from operator import itemgetter
from argparse import ArgumentParser

import logger
import distance
from output import Output
from parser import WSJParser
from corpus import Corpus, FragmentedCorpus
from similarity import ComparisonPerCPU as Similarity

log = logger.getlogger(True)

arguments = ArgumentParser()
arguments.add_argument('--input-directory')
arguments.add_argument('--output-directory')
arguments.add_argument('--corpus-pickle')
arguments.add_argument('--fragment-pickle')
args = arguments.parse_args()

output = Output(args.output_directory)

#
# Build the corpus
#
if args.corpus_pickle:
    with open(args.corpus_pickle, 'rb') as fp:
        corpus = pickle.load(fp)
else:
    parser = WSJParser()
    documents = parser.parse(args.input_directory)
    corpus = Corpus(sorted(documents, key=itemgetter(0)))
    output.to_pickle('corpus', corpus)

for i in [ 'documents', 'characters' ]:
    f = getattr(corpus, i)
    log.info('{0}: {1}'.format(i, f()))

#
# Build the fragments
#
if args.fragment_pickle:
    with open(args.fragment_pickle, 'rb') as fp:
        fragments = pickle.load(fp)
else:
    fragments = FragmentedCorpus(corpus)
    output.to_pickle('fragments', fragments)

log.info('Fragments {0}'.format(len(fragments)))

#
# Build the similarity matrix
#
matrix = Similarity(fragments)
output.to_pickle('wsj-matrix', matrix)
matrix.dotplot(str(output.fpath('wsj', 'png')))
