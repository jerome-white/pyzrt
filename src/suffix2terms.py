import csv
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser

from zrtlib import logger
from zrtlib.suffix import suffix_builder
from zrtlib.tokenizer import TokenSet, unstream
from zrtlib.pseudoterm import PseudoTermWriter

def f(jobs, path):
    log = logger.getlogger()
    fieldnames = [ 'term', 'ngram', 'start', 'end' ]

    while True:
        (term, ngram, collection) = jobs.get()
        log.info('{0} |{1}|'.format(term, ngram))

        for token in collection:
            for i in token:
                row = dict(zip(fieldnames, [ term, ngram, i.start, i.end ]))
                p = path.joinpath(i.docno.stem)

                with p.open('a') as fp:
                    writer = csv.DictWriter(fp, fieldnames=fieldnames)
                    if fp.tell() == 0:
                        writer.writeheader()
                    writer.writerow(row)

        jobs.task_done()

arguments = ArgumentParser()
arguments.add_argument('--suffix-tree', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--term-prefix', default='pt')
args = arguments.parse_args()

jobs = mp.JoinableQueue()

with mp.Pool(initializer=f, initargs=(jobs, args.output)):
    log.info('suffix tree')
    suffix = suffix_builder(args.suffix_tree, unstream, TokenSet)
    ngrams = len(str(len(suffix)))

    for (i, (ngram, collection)) in enumerate(suffix.each()):
        term = args.term_prefix + str(i).zfill(ngrams)
        jobs.put((term, ngram, collection))
    jobs.join()
