import sys
import csv
import corpus

from parser import NameSortedCorpus
from pathlib import Path
from argparse import ArgumentParser

arguments = ArgumentParser()
arguments.add_argument('--corpus-directory')
arguments.add_argument('--block-size', default=1, type=int)
args = arguments.parse_args()

corpus_listing = NameSortedCorpus(args.corpus_directory)
writer = csv.writer(sys.stdout)
for row in corpus.fragment(corpus_listing, args.block_size):
    writer.writerow(row)
