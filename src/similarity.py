import csv
import operator as op
from pathlib import Path
from argparse import ArgumentParser
from itertools import combinations
from collections import namedtuple
from multiprocessing import Pool

from zrtlib import logger
from zrtlib.post import Posting
from zrtlib.corpus import Corpus
from zrtlib.dotplot import DistributedDotplot
from zrtlib.tokenizer import Segmenter, CorpusTokenBuilder

def func(args):
    (posting, index, cli) = args
    
    log = logger.getlogger()
    log.info(index)
    
    elements = int(posting)
    
    if cli.max_elements > 0:
        compression_ratio = cli.max_elements / elements
    else:
        compression_ratio = cli.compression
        
    dp = DistributedDotplot(elements, compression_ratio, cli.mmap)
    weight = posting.weight(index)

    for i in filter(lambda x: op.ne(*x), combinations(posting.each(index), 2)):
        dp.update(*i, weight)

def enumeration(posting, args):
    for i in posting.keys():
        if i.isalpha() and posting.mass(i) < args.threshold:
            yield (posting, i, args)

arguments = ArgumentParser()
arguments.add_argument('--mmap')
arguments.add_argument('--output-image')
arguments.add_argument('--tokens', type=Path)
arguments.add_argument('--corpus', type=Path)
arguments.add_argument('--threshold', default=1, type=float)
arguments.add_argument('--compression', default=1, type=float)
arguments.add_argument('--max-elements', type=float)
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

# dots = np.memmap(args.mmap, dtype=np.float16, mode='r', sha
