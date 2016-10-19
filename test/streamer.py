from pathlib import Path
from argparse import ArgumentParser

from zrtlib.corpus import CompleteCorpus, WindowStreamer
from zrtlib.tokenizer import Tokenizer

arguments = ArgumentParser()
arguments.add_argument('--corpus', type=Path)
arguments.add_argument('--skip', type=int, default=0)
arguments.add_argument('--offset', type=int, default=0)
arguments.add_argument('--block-size', type=int, default=1)
args = arguments.parse_args()

corpus = CompleteCorpus(args.corpus)
stream = WindowStreamer(corpus, args.block_size, args.skip, args.offset)
tokenizer = Tokenizer(stream)

for (i, j) in tokenizer:
    print(i, repr(j), j.tostring(corpus))
