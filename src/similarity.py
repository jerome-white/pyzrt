import csv
import operator as op
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
    (key, indices, weight, dpargs) = args

    log = logger.getlogger()
    log.info('|{0}| {1}'.format(key, len(indices)))

    dp = DistributedDotplot(*dpargs)
    for (i, j) in combinations(indices, 2):
        dp.update(i, j, weight)

    return key

def mkfname(original):
    (*parts, name) = original.parts

    while True:
        (c, _) = str(uuid4()).split('-', 1)
        fname = name + '-' + c
        path = Path(*parts, fname)
        if not path.exists():
            return path

def enumeration(posting, args, ledger, dpargs):
    f = lambda x: x not in ledger and posting.mass(x) < args.threshold
    keys = filter(f, posting.keys())

    for i in islice(keys, args.node, None, args.total_nodes):
        weight = posting.weight(i)
        indices = list(posting.each(i))

        yield (i, indices, weight, dpargs)

###########################################################################

arguments = ArgumentParser()
# arguments.add_argument('--tokens', actions='append', type=Path)
arguments.add_argument('--tokens', type=Path)
arguments.add_argument('--corpus', type=Path)
arguments.add_argument('--ledger', type=Path)

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

log.info('initialise dotplot')
elements = int(posting)
mmap = mkfname(args.mmap)
if args.max_elements > 0:
    compression = args.max_elements / elements
else:
    compression = args.compression
dpargs = (elements, compression, mmap)

if args.ledger:
    with args.ledger.open() as fp:
        ledger = set(map(op.methodcaller('strip'), fp.readlines()))
    scribe = args.ledger.open('a')
    annotate = lambda x: print(x, file=scribe)
else:
    ledger = set()
    annotate = lambda x: None

log.info('working: {0}'.format(elements))
dp = DistributedDotplot(elements, compression, mmap, True)
with mp.Pool() as pool:
    iterable = enumeration(posting, args, ledger, dpargs)
    for i in pool.imap_unordered(func, iterable):
        annotate(i)
dp.dots.flush()
log.info('complete')

if args.ledger:
    scribe.close()
