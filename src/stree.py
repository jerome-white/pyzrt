import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser

import numpy as np

from zrtlib import logger
from zrtlib.corpus import Corpus
from zrtlib.suffix import SuffixTree
from zrtlib.tokenizer import WindowSequencer, Tokenizer

def func(corpus_directory, incoming, outgoing):
    log = logger.getlogger()

    corpus = Corpus(corpus_directory)

    log.debug('ready')
    while True:
        job = incoming.get()
        log.info(', '.join(map(str, job.values())))

        sequencer = WindowSequencer(corpus=corpus, **job)
        tokenizer = Tokenizer(sequencer)

        for (_, i) in tokenizer:
            kwargs = { 'ngram': i.tostring(corpus), 'token': i }
            outgoing.put(kwargs)
        outgoing.put(None)

log = logger.getlogger()

arguments = ArgumentParser()
arguments.add_argument('--corpus', type=Path)
arguments.add_argument('--min-gram', type=int, default=1)
arguments.add_argument('--max-gram', type=int, default=np.inf)
args = arguments.parse_args()

workers = mp.cpu_count()
outgoing = mp.Queue()
incoming = mp.Queue()

log.info('>| begin')
with mp.Pool(initializer=func, initargs=(args.corpus, outgoing, incoming, )):
    suffix = SuffixTree()

    for i in range(args.min_gram, args.max_gram):
        log.info('{0}-gram'.format(i))
        outstanding = 0

        for j in range(workers):
            kwargs = { 'block_size': i, 'skip': j }
            outgoing.put(kwargs)
            outstanding += 1

        while outstanding > 0:
            result = incoming.get()
            if result is None:
                outstanding -= 1
            else:
                suffix.add(root_key_length=args.min_gram, **result)
log.info('>| end')

log.info('> pickle')
import pickle
with open('/scratch/jsw7/zrt/wsj/suffix.pkl', 'wb') as fp:
    pickle.dump(suffix, fp)
log.info('< pickle')