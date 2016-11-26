import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile

from scipy import constants

from zrtlib import zutils
from zrtlib import logger
from zrtlib.suffix import SuffixTree
from zrtlib.corpus import CompleteCorpus, WindowStreamer
from zrtlib.tokenizer import Tokenizer, TokenSet, unstream

def func(corpus_directory, incoming, outgoing):
    log = logger.getlogger()

    corpus = CompleteCorpus(corpus_directory)
    while True:
        log.info('ready')
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
arguments.add_argument('--prune', type=int, default=0)
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
arguments.add_argument('--min-gram', type=int, default=1)
arguments.add_argument('--max-gram', type=int)
arguments.add_argument('--incremental', action='store_true')
args = arguments.parse_args()

incoming = mp.Queue()
outgoing = mp.Queue()

#
# Work!
#
log.info('>| begin')

workers = min(mp.cpu_count(), max(1, args.workers))
if workers != args.workers:
    log.warning('Worker request adjusted -> {0}'.format(workers))
initargs = (args.corpus, outgoing, incoming)

with mp.Pool(processes=workers, initializer=func, initargs=initargs):
    if args.existing:
        log.info('+ existing')
        suffix = Suffix.builder(args.existing, unstream, TokenSet)
        (min_gram, max_gram) = zutils.minmax(suffix.lf().keys())
        if args.min_gram <= max_gram:
            args.min_gram = max_gram + 1
            msg = 'Largest existing n-gram {0}. New starting n-gram {1}'
            log.warning(msg.format(max_gram, args.min_gram))
        log.info('- existing ({0} {1})'.format(min_gram, args.min_gram))
    else:
        suffix = SuffixTree(TokenSet)
        min_gram = args.min_gram

    plogger = logger.PeriodicLogger(constants.minute * 5)
    fname = '{{0:0{0:d}d}}'.format(len(str(args.max_gram)))

    #
    # Create the work queue
    #
    for i in zutils.count(args.min_gram, args.max_gram):
        log.info('setup {0}'.format(i))
        jobs = 0
        for j in range(workers):
            outgoing.put((i, workers, j))
            jobs += 1

        #
        # Use the results to build a suffix tree
        #
        log.info('process {0}'.format(jobs))
        while jobs > 0:
            value = incoming.get()
            if value is None:
                jobs -= 1
            else:
                (ngram, token) = value
                suffix.add(ngram, token, min_gram)
                plogger.emit('+{0}|{1}|'.format(len(ngram), ngram))

        #
        # Prune and fold the tree
        #
        log.info('trim')
        if args.prune > 0:
            remaining = suffix.prune(args.prune)
            log.info('- pruned {0}'.format(remaining))
        suffix.compress(i)

        #
        # Save
        #
        if args.incremental or i == args.max_gram:
            path = args.output.join(fname.format(i))
            with path.with_suffix('.csv').open('w') as fp:
                log.info(fp.name)
                suffix.write(fp)

log.info('<| complete')
