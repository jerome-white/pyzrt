import csv
import similarity

from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Manager

arguments = ArgumentParser()
arguments.add_argument('--corpus-directory')
arguments.add_argument('--fragment-file')
args = arguments.parse_args()

with Manager() as manager:
    corpus = manager.dict()
    path = Path(args.corpus_directory)
    for i in path.iterdir():
        with i.open() as fp:
            corpus[i.name] = fp.read()
    similarity.pairs(corpus, args.fragment_file)
