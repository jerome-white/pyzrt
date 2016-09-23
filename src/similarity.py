import csv
import operator as op
from pathlib import Path
from argparse import ArgumentParser
from itertools import islice, combinations
from collections import namedtuple
from multiprocessing import Pool

from zrtlib import logger
from zrtlib.post import Posting
from zrtlib.corpus import Corpus
from zrtlib.dotplot import DistributedDotplot
from zrtlib.tokenizer import Segmenter, CorpusTokenBuilder

Args = namedtuple('Args', 'index, elements, weight, indices, opts')

def func(args):
    log = logger.getlogger()
    log.info('{0}: {1}'.format(args.index, args.elements))
    
    o = args.opts
    c = o.max_elements / args.elements if o.max_elements > 0 else o.compression
    dp = DistributedDotplot(args.elements, c, args.opts.mmap)

    for (i, j) in filter(lambda x: op.ne(*x), combinations(args.indices, 2)):
        dp.update(i, j, args.weight)

    dp.dots.flush()

def enumeration(posting, args):
    elements = int(posting)

    for i in islice(posting.keys(), args.node, None, args.total_nodes):
        if i.isalpha() and posting.mass(i) < args.threshold:
            weight = posting.weight(i)
            indices = list(posting.each(i))

            yield Args(i, elements, weight, indices, args)

arguments = ArgumentParser()
arguments.add_argument('--tokens', type=Path)
arguments.add_argument('--corpus', type=Path)

arguments.add_argument('--mmap', type=Path)
arguments.add_argument('--threshold', default=1, type=float)
arguments.add_argument('--compression', default=1, type=float)
arguments.add_argument('--max-elements', default=0, type=float)

arguments.add_argument('--node', type=int, default=0)
arguments.add_argument('--total-nodes', type=int, default=1)
args = arguments.parse_args()

log = logger.getlogger(True)

log.info('postings')
with args.tokens.open() as fp:
    reader = Segmenter(csv.reader(fp))

    # builder = lambda x: str(FileTokenBuilder(x, args.corpus))
    corpus = Corpus(args.corpus)
    builder = lambda x: str(CorpusTokenBuilder(x, corpus))

    posting = Posting(reader, builder)

log.info('working')
with Pool() as pool:
    for _ in pool.imap_unordered(func, enumeration(posting, args)):
        pass
