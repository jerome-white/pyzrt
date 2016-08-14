import sys
import csv
import corpus

from pathlib import Path
from archive import NamedSortedCorpus
from argparse import ArgumentParser

arguments = ArgumentParser()
arguments.add_argument('--corpus-directory')
args = arguments.parse_args()

corpus_listing = NamedSortedCorpus(arguments.corpus_directory)
writer = csv.writer(sys.stdout)
for row in corpus.fragment(corpus_listing):
    writer.writerow(row)
