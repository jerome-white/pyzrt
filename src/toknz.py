import sys
import csv
from pathlib import Path
from argparse import ArgumentParser

from zrtlib.tokenizer import CharacterTokenizer

arguments = ArgumentParser()
arguments.add_argument('--corpus', type=Path)
arguments.add_argument('--block-size', default=1, type=int)
args = arguments.parse_args()

corpus = sorted(args.corpus_directory.iterdir())
tokenizer = CharacterTokenizer(corpus, args.block_size)
writer = csv.writer(sys.stdout)
for (key, token) in tokenizer.tokenize():
    writer.writerow([ key ] + dir(token))
