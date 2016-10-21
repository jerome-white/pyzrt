import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile

from scipy import constants

from zrtlib import zutils
from zrtlib import logger
from zrtlib.suffix import SuffixTree
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
    increments = []
    plogger = logger.PeriodicLogger(constants.minute * 5)

    suffix = SuffixTree()
    if args.existing:
        log.info('+ existing')
        suffix.read(args.existing, unstream)
        args.min_gram = zutils.minval(suffix.each()) + 1
        log.info('- existing ({0})'.format(args.min_gram))

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
                suffix.add(ngram, token, args.min_gram)
                plogger.emit('+{0}|{1}|'.format(len(ngram), ngram))

        #
        # Prune and fold the tree
        #
        if args.prune > 0:
            remaining = suffix.prune(args.prune)
            log.info('pruned {0}'.format(remaining))
        suffix.fold()

        #
        # Dump if needed
        #
        if args.incremental:
            sfx = '.' + str(i)
            with NamedTemporaryFile(mode='w', suffix=sfx, delete=False) as fp:
                suffix.write(fp)
                increments.append(Path(fp.name))
                log.info('incremental {0}'.format(fp.name))

#
# Save the output
#
if args.output:
    if increments:
        latest = increments.pop()
        latest.rename(args.output)
    else:
        log.info('+ output')
        with args.output.open('w') as fp:
            suffix.write(fp)
        log.info('- output')

for i in increments:
    i.unlink()

log.info('<| complete')
