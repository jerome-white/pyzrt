import csv

from argparse import ArgumentParser
from multiprocessing import Manager

arguments = ArgumentParser()
arguments.add_argument('--corpus-directory')
arguments.add_argument('--fragment-file')
args = arguments.parse_args()

with open(arguments.corpus_directory) as fp:
    reader = csv.reader(fp)
    with Manager() as manager:
        corpus = manager.dict()
        corpus.update({ docno: data for (docno, data) in reader })

        similarity.pairs(corpus, arguments.fragment_file)
