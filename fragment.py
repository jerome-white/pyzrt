import sys
import csv
import corpus

from parser import NameSortedCorpus
from pathlib import Path
from argparse import ArgumentParser

arguments = ArgumentParser()
arguments.add_argument('--corpus-directory')
args = arguments.parse_args()

corpus_listing = NameSortedCorpus(args.corpus_directory)
writer = csv.writer(sys.stdout)
for row in corpus.fragment(corpus_listing):
    writer.writerow(row)
