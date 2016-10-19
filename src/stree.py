import queue
import operator as op
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile
from collections import Counter

import numpy as np
from scipy import constants

from zrtlib import zutils
from zrtlib import logger
from zrtlib.suffix import SuffixTree
from zrtlib.queues import ConsumptionQueue
from zrtlib.corpus import CompleteCorpus, WindowStreamer
from zrtlib.tokenizer import Tokenizer, unstream

def func(corpus_directory, incoming, outgoing):
    log = logger.getlogger()

    corpus = CompleteCorpus(corpus_directory)
    log.debug('ready')
    while True:
        (block_size, skip, offset) = incoming.get()
        log.info(','.join(map(str, [ block_size, offset ])))

        stream = WindowStreamer(corpus, block_size, skip, offset)
        tokenizer = Tokenizer(stream)

        for (_, i) in tokenizer:
            ngram = i.tostring(corpus)
            outgoing.put((ngram, i))
        outgoing.put(None)

#
# Setup the variables
#
log = logger.getlogger()

arguments = ArgumentParser()
arguments.add_argument('--corpus', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--existing', type=Path)
arguments.add_argument('--min-gram', type=int, default=1)
arguments.add_argument('--max-gram', type=int, default=np.inf)
arguments.add_argument('--incremental', action='store_true')
args = arguments.parse_args()

incoming = mp.Queue()
outgoing = mp.Queue()

#
# Work!
#
log.info('>| begin')
with mp.Pool(initializer=func, initargs=(args.corpus, outgoing, incoming)):
    workers = mp.cpu_count()

    suffix = SuffixTree()
    if args.existing:
        log.info('+ existing')
        suffix.read(args.existing, unstream)
        args.min_gram = zutils.minval(suffix.each()) + 1
        log.info('- existing {0}'.format(len(c)))

    #
    # Create the work queue
    #
    for i in range(args.min_gram, args.max_gram + 1):
        log.info('+| setup {0}'.format(i))
        jobs = 0
        for j in range(workers):
            outgoing.put((i, workers, j))
            jobs += 1

        #
        # Use the results to build a suffix tree
        #
        log.info('+| process {0}'.format(jobs))
        plogger = logger.PeriodicLogger(constants.minute * 5)
        while jobs > 0:
            value = incoming.get()
            if value is None:
                jobs -= 1
            else:
                (ngram, token) = value
                plogger.emit('added ' + ngram)
                suffix.add(ngram, token, args.min_gram)

        #
        # Dump if needed
        #
        if args.output and (args.incremental or i == args.max_gram):
            log.info('+ output')
            suffix.write(args.output)
            log.info('- output')
log.info('<| complete')
