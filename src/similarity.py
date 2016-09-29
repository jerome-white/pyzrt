import csv
import multiprocessing as mp
from uuid import uuid4
from pathlib import Path
from argparse import ArgumentParser
from itertools import islice, combinations

from zrtlib import logger
from zrtlib.post import Posting
from zrtlib.corpus import Corpus
from zrtlib.dotplot import DistributedDotplot
from zrtlib.tokenizer import Tokenizer, CorpusTranscriber

def func(args):
    (key, indices, weight, dpopts) = args

    log = logger.getlogger()
    log.info('{0} {1}'.format(key, len(indices)))

    dp = DistributedDotplot(*dpopts)

    for (i, j) in combinations(indices, 2):
        dp.update(i, j, weight)

    dp.dots.flush()

    return key

def mkfname(original):
    (*parts, name) = original.parts

    while True:
        (c, _) = str(uuid4()).split('-', 1)
        fname = name + '-' + c
        path = Path(*parts, fname)
        if not path.exists():
            return path

def enumeration(posting, args):
    elements = int(posting)
    mmap = mkfname(args.mmap)
    if args.max_elements > 0:
        compression = args.max_elements / elements
    else:
        compression = args.compression

    #
    # Divide the Sequences across the nodes...
    #
    keys = filter(lambda x: posting.mass(x) < args.threshold, posting.keys())
    for i in islice(keys, args.node, None, args.total_nodes):
        weight = posting.weight(i)
        values = list(posting.each(i))

        yield (i, values, weight, (elements, compression, mmap))

###########################################################################

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
    for i in pool.imap_unordered(func, enumeration(posting, args)):
        log.info('finished {0}'.format(i))
log.info('complete')
