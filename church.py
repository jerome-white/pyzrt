import operator as op
from argparse import ArgumentParser
from itertools import combinations, filterfalse

import numpy as np

from dots import dotplot
from corpus import from_disk
from posting import Posting, Dotplot

arguments = ArgumentParser()
arguments.add_argument('--output-image')
arguments.add_argument('--fragment-file')
arguments.add_argument('--corpus-directory')
arguments.add_argument('--threshold', default=np.inf, type=float)
arguments.add_argument('--compression-ratio', default=1, type=float)
args = arguments.parse_args()

corpus = dict(from_disk(args.corpus_directory))
elements = sum([ len(x) for x in corpus.values() ])
dp = Dotplot(elements, compression_ratio=args.compression_ratio)

with open(args.fragment_file) as fp:
    posting = Posting(fp, corpus)

equality = lambda x: op.eq(*x)

for i in posting.posting.keys():
    if i.frequency() < args.threshold: # and i.isalpha():
        weight = posting.weight(i)
        for (x, y) in filterfalse(equality, combinations(posting.each(i), 2)):
            dp.update(x, y, weight)

dotplot(dp.dots, args.output_image)
