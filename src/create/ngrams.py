#
# Parses a directory of files into n-grams. If max-gram's are
# specified, then the set will be of variable length (between min-gram
# and max-gram); it will be of constant size otherwise.
#
# Generally, files are assumed to have already been parsed;
# specifically, that is, not in the TREC format.
#

import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser

from zrtlib import logger
from zrtlib import zutils

def func(incoming, output_directory, n, m=None):
    log = logger.getlogger()
    collection = []

    if m is None:
        m = n
    assert(0 < n <= m)
    window = deque(maxlen=m)

    while True:
        document = incoming.get()
        log.info(document.stem)

        for i in (window, collection):
            i.clear()

        with document.open() as fp:
            while True:
                c = fp.read(1)
                if c:
                    window.append(c)
                else:
                    window.popleft()
                    if len(window) < n:
                        break

                if len(window) >= n:
                    ngram = ''.join(window).replace(' ', '_')
                    collection.append(ngram)

        if collection:
            o = output_directory.joinpath(document.stem)
            with o.open('w') as fp:
                print(*collection, file=fp)
        else:
            log.warning(document.stem)

        incoming.task_done()

arguments = ArgumentParser()
arguments.add_argument('--documents', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--min-gram', type=int)
arguments.add_argument('--max-gram', type=int)
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
args = arguments.parse_args()

log = logger.getlogger(True)
log.info('>| begin')

document_queue = mp.JoinableQueue()
initargs = (document_queue, args.output, args.min_gram, args.max_gram)

with mp.Pool(processes=args.workers, initializer=func, initargs=initargs):
    for i in zutils.walk(args.documents):
        document_queue.put(i)
    document_queue.join()

log.info('<| complete')
