import sys
import csv
from pathlib import Path
from argparse import ArgumentParser

from zrtlib.tokenizer import WindowedSequencer

arguments = ArgumentParser()
arguments.add_argument('--corpus', type=Path)
arguments.add_argument('--block-size', default=1, type=int)
args = arguments.parse_args()

corpus = sorted(args.corpus.iterdir())
sequencer = WindowedSequencer(corpus, args.block_size)
writer = csv.writer(sys.stdout)
for (key, char) in sequencer.sequence():
    writer.writerow([ key ] + char.tolist())
