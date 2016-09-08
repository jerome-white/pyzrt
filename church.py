import operator as op
from argparse import ArgumentParser
from itertools import combinations
from collections import namedtuple
from multiprocessing import Pool

import logger
from dots import dotplot
from corpus import from_disk
from posting import Posting, DistributedDotplot

Args = namedtuple('Args', 'dotplot, weight, coordinates')

def func(args):
    args.dotplot.update(*args.coordinates, args.weight)

arguments = ArgumentParser()
arguments.add_argument('--mmap')
arguments.add_argument('--output-image')
arguments.add_argument('--fragment-file')
arguments.add_argument('--corpus-directory')
arguments.add_argument('--threshold', default=1, type=float)
arguments.add_argument('--compression', default=1, type=float)
arguments.add_argument('--max-elements', type=float)
args = arguments.parse_args()

log = logger.getlogger(True)

log.info('corpus')
corpus = dict(from_disk(args.corpus_directory))

log.info('postings')
with open(args.fragment_file) as fp:
    posting = Posting(fp, corpus)

log.info('dotplot')
elements = sum([ len(x) for x in corpus.values() ])
c = args.max_elements / elements if args.max_elements > 0 else args.compression
dp = DistributedDotplot(elements, c, args.mmap)

with Pool() as pool:
    for i in posting.keys():
        if i.isalpha() and posting.mass(i) <= args.threshold:
            log.info('+ {0}'.format(i))

            weight = posting.weight(i)

            iterable = map(lambda x: Args(dp, weight, x),
                           filter(lambda x: op.ne(*x),
                                  combinations(posting.each(i), 2)))
            for _ in pool.map(func, iterable):
                pass

            log.info('- {0}'.format(i))
    
dotplot(dp.dots, args.output_image)
