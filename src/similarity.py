import csv
import multiprocessing as mp
from uuid import uuid4
from pathlib import Path
from argparse import ArgumentParser
from itertools import islice, combinations

from zrtlib import logger
from zrtlib.post import Posting
from zrtlib.ledger import Ledger
from zrtlib.corpus import Corpus
from zrtlib.dotplot import Dotplot
from zrtlib.jobqueue import Job, JobQueue
from zrtlib.tokenizer import Tokenizer, CorpusTranscriber

def func(queue):
    log = logger.getlogger()

    while True:
        job = queue.get()
        log.info('|{0}| {1}'.format(job.key, len(job.indices)))

        for (i, j) in combinations(job.indices, 2):
            dp.update(i, j, job.weight)

        queue.task_done(key)

def mkfname(original):
    (*parts, name) = original.parts

    while True:
        (c, _) = str(uuid4()).split('-', 1)
        fname = name + '-' + c
        path = Path(*parts, fname)
        if not path.exists():
            return path

def enumeration(posting, args, ledger):
    f = lambda x: x not in ledger and posting.mass(x) < args.threshold
    keys = filter(f, posting.keys())

    for i in islice(keys, args.node, None, args.total_nodes):
        weight = posting.weight(i)
        indices = list(posting.each(i))

        yield (i, indices, weight)

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

log.info('starting')
with Ledger(args.ledger, args.node) as ledger:
    queue = JobQueue(ledger)
    with mp.Pool(initializer=func, initargs=(queue, )) as pool:
        
        log.info('initialise: posting')
        # builder = lambda x: str(FileTranscriber(x, args.corpus))
        corpus = Corpus(args.corpus)
        builder = lambda x: str(CorpusTranscriber(x, corpus))
        with args.tokens.open() as fp:
            reader = Tokenizer(csv.reader(fp))
            posting = Posting(reader, builder)

        log.info('initialise: dotplot')
        elements = int(posting)
        if args.max_elements > 0:
            compression = args.max_elements / elements
        else:
            compression = args.compression
        dp = Dotplot(elements, args.mmap, compression)

        log.info('working: {0}'.format(elements))
        for i in enumeration(posting, args, ledger):
            job = Job(*i, dp)
            queue.put(job)
        queue.join()

        dp.matrix.flush()
log.info('complete')
