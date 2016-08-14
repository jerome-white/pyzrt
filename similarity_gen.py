
import sys
import csv
import corpus

from pathlib import Path
from archive import NamedSortedCorpus
from argparse import ArgumentParser

arguments = ArgumentParser()
arguments.add_argument('--corpus-directory')
arguments.add_argument('--fragment-directory')
args = arguments.parse_args()

with open(arguments.corpus_directory) as fp:
    reader = csv.reader(fp)
    with Manager() as manager:
        d = manager.dict()
        d.update({ docno: data for (docno, data) in reader })

        similarity.pairs
