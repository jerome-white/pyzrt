import queue
import pickle
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile

import numpy as np
from scipy import constants

from zrtlib import logger
from zrtlib.suffix import SuffixTree
from zrtlib.queues import ConsumptionQueue
from zrtlib.corpus import CompleteCorpus, WindowStreamer
from zrtlib.tokenizer import Tokenizer

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
arguments.add_argument('--pickle', type=Path)
arguments.add_argument('--min-gram', type=int, default=1)
arguments.add_argument('--max-gram', type=int, default=np.inf)
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

    #
    # Create the work queue
    #
    for i in range(args.min_gram, args.max_gram):
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
        # Pickle if needed
        #
        if args.pickle:
            log.info('+ pickle')
            d = str(args.pickle.parent)
            with NamedTemporaryFile(mode='wb', dir=d, delete=False) as fp:
                pickle.dump(suffix, fp)
                tmp = Path(fp.name)
            tmp.rename(args.pickle)
            log.info('- pickle')
log.info('<| complete')
