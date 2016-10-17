import sys
import queue
import pickle
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser

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
        try:
            (block_size, skip, offset) = incoming.get()
        except queue.Empty:
            break
        log.info(','.join(map(str, [ block_size, offset ])))

        stream = WindowStreamer(corpus, block_size, skip, offset)
        tokenizer = Tokenizer(stream)

        for (_, i) in tokenizer:
            ngram = i.tostring(corpus)
            outgoing.put((ngram, i))

        incoming.task_done()
    log.debug('finished')

log = logger.getlogger()

arguments = ArgumentParser()
arguments.add_argument('--corpus', type=Path)
arguments.add_argument('--pickle', type=Path)
arguments.add_argument('--min-gram', type=int, default=1)
arguments.add_argument('--max-gram', type=int, default=np.inf)
args = arguments.parse_args()

incoming = mp.Queue()
outgoing = ConsumptionQueue()

log.info('>| begin')
with mp.Pool(initializer=func, initargs=(args.corpus, outgoing, incoming, )):
    workers = mp.cpu_count()
    
    log.info('+| setup')
    for i in range(args.min_gram, args.max_gram):
        for j in range(workers):
            outgoing.put((i, workers, j))

    log.info('+| process')
    suffix = SuffixTree()
    plogger = logger.PeriodicLogger(constants.minute * 15)
    while not outgoing.empty():
        outgoing.barrier.set()
        (ngram, token) = incoming.get()
        suffix.add(ngram, token, args.min_gram)

        plogger.emit(sys.getsizeof(suffix))

if args.pickle:
    log.info('+ pickle')
    with args.pickle.open('wb') as fp:
        pickle.dump(suffix, fp)
    log.info('- pickle')
log.info('<| complete')
