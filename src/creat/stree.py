import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile

from scipy import constants

import zrtlib.tokenizer as tkn
from zrtlib import zutils
from zrtlib import logger
from zrtlib.suffix import SuffixTree
from zrtlib.corpus import CompleteCorpus, WindowStreamer

def func(incoming, outgoing, corpus_directory, Tokenizer, Streamer):
    log = logger.getlogger()

    corpus = CompleteCorpus(corpus_directory)
    while True:
        log.info('ready')
        (block_size, skip, offset) = incoming.get()
        log.info(','.join(map(str, [ block_size, offset ])))

        tokenizer = Tokenizer(Streamer(corpus, block_size, skip, offset))
        for (_, i) in tokenizer:
            ngram = i.tostring(corpus)
            outgoing.put((ngram, i))
        outgoing.put(None)

#
# Setup the variables
#
log = logger.getlogger(True)

arguments = ArgumentParser()
arguments.add_argument('--input', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--existing', type=Path)
arguments.add_argument('--prune', type=int, default=0)
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
arguments.add_argument('--min-gram', type=int, default=1)
arguments.add_argument('--max-gram', type=int)
arguments.add_argument('--no-compress', action='store_true')
arguments.add_argument('--incremental', action='store_true')
arguments.add_argument('--document-boundaries', action='store_true')
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

if args.document_boundaries:
    tokenizer = tkn.BoundaryTokenizer
else:
    tokenizer = tkn.Tokenizer
streamer = WindowStreamer

initargs = (outgoing, incoming, args.input, tokenizer, streamer)

with mp.Pool(processes=workers, initializer=func, initargs=initargs):
    if args.existing:
        log.info('+ existing')
        suffix = SuffixTree.builder(args.existing, tkn.unstream, tkn.TokenSet)
        (min_gram, max_gram) = zutils.minmax(suffix.lf().keys())
        if args.min_gram <= max_gram:
            args.min_gram = max_gram + 1
            msg = 'Largest existing n-gram {0}. New starting n-gram {1}'
            log.warning(msg.format(max_gram, args.min_gram))
        log.info('- existing ({0} {1})'.format(min_gram, args.min_gram))
    else:
        suffix = SuffixTree(tkn.TokenSet)
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
        if not args.no_compress:
            suffix.compress(i)

        #
        # Save
        #
        if args.incremental or i == args.max_gram:
            path = args.output.joinpath(fname.format(i))
            with path.with_suffix('.csv').open('w', buffering=1) as fp:
                log.info(fp.name)
                suffix.write(fp)

log.info('<| complete')
