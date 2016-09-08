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
    log.info('dotplot')
    elements = posting.tokens()
    c = args.max_elements / elements if args.max_elements > 0 else args.compression
    
    dp = DistributedDotplot(elements, c, args.mmap)
    weight = posting.weight(token)

    for (i, j) in filter(lambda x: op.ne(*x), combinations(posting.each(i), 2)):
        dp.update(i, j, weight)

def enumeration(posting, threshold):
    for i in posting.keys():
        if i.isalpha() and posting.mass(i) <= threshold:
            elements = posting.tokens()
            yield Args(posting)

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

log.info('postings')
with open(args.fragment_file) as fp:
    kwargs = { 'corpus_directory': args.corpus_directory }
    posting = Posting(fp, **kwargs)

with Pool() as pool:
    for _ pool.imap_unordered(func, enumeration(posting, args.threshold)):
        pass
    
dotplot(dp.dots, args.output_image)
