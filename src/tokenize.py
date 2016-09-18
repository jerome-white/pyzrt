import sys
import csv
from pathlib import Path
from argparse import ArgumentParser

from corpus import NameSortedCorpus

arguments = ArgumentParser()
arguments.add_argument('--corpus-directory')
arguments.add_argument('--block-size', default=1, type=int)
args = arguments.parse_args()

path = Path(corpus_directory)
assert(path.is_dir())
writer = csv.writer(sys.stdout)
tokenizer = CharacterTokenizer(path.iterdir(), args.block_size)
for (key, token) in tokenizer:
    writer.writerow([ key ] + list(token))
