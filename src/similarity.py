import csv
import operator as op
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from itertools import islice, combinations

from zrtlib import logger
from zrtlib.post import Posting
from zrtlib.corpus import Corpus
from zrtlib.dotplot import DistributedDotplot
from zrtlib.tokenizer import Tokenizer, CorpusTranscriber

def func(args):
    (indices, weight, *dpopts) = args

    dp = DistributedDotplot(*dpopts)
    for (i, j) in indices:
        dp.update(i, j, weight)
    dp.dots.flush()

def enumeration(posting, args):
    cpus = mp.cpu_count()
    elements = int(posting)

    if args.max_elements > 0:
        compression = args.max_elements / elements
    else:
        compression = args.compression

    #
    # Divide the keys across the nodes
    #
    for i in islice(posting.keys(), args.node, None, args.total_nodes):
        if i.isalpha() and posting.mass(i) < args.threshold:
            weight = posting.weight(i)
            pairs = filter(lambda x: op.ne(*x),
                           combinations(posting.each(i), 2))

            #
            # Divide the regions of the matrix across the processors
            #
            for j in range(cpus):
                k = list(islice(pairs, j, None, cpus))
                log.info('partition: {0} {1} {2}'.format(i, j, len(k)))

                yield (k, weight, elements, compression, args.mmap)

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
    reader = Tokenizer(csv.reader(fp))

    # builder = lambda x: str(FileTranscriber(x, args.corpus))
    corpus = Corpus(args.corpus)
    builder = lambda x: str(CorpusTranscriber(x, corpus))

    posting = Posting(reader, builder)

log.info('working')
with mp.Pool() as pool:
    for _ in pool.imap_unordered(func, enumeration(posting, args)):
        pass
