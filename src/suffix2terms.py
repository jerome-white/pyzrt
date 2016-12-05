import csv
import itertools
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from collections import namedtuple, defaultdict

from zrtlib import logger
from zrtlib.query import QueryDoc
from zrtlib.corpus import Character

Term = namedtuple('Term', 'term, ngram, start, end')

def func(jobs, path):
    log = logger.getlogger()

    while True:
        (document, terms) = jobs.get()
        log.info('{0} {1}'.format(document.stem, len(terms)))

        p = path.joinpath(document.stem)
        with p.open('w') as fp:
            writer = csv.DictWriter(fp, fieldnames=Term._fields)
            writer.writeheader()
            for i in terms:
                writer.writerow(i._asdict())

        jobs.task_done()

arguments = ArgumentParser()
arguments.add_argument('--suffix-tree', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--term-prefix', default='pt')
arguments.add_argument('--documents-only', action='store_true')
args = arguments.parse_args()

log = logger.getlogger(True)
jobs = mp.JoinableQueue()

log.info('>| begin')
with mp.Pool(initializer=func, initargs=(jobs, args.output)):
    postings = defaultdict(list)

    with args.suffix_tree.open() as fp:
        # count the number of terms
        for (i, _) in enumerate(fp):
            pass
        log.info('terms {0}'.format(i))
        digits = len(str(i))
        fp.seek(0)

        reader = csv.reader(fp)
        for (i, (ngram, *tokens)) in enumerate(reader):
            prefix = args.term_prefix + str(i).zfill(digits)
            for j in tokens:
                toks = j.split()
                for k in range(0, len(toks), 3):
                    char = Character.fromlist(toks[k:k+3])
                    if args.document_only and QueryDoc.isquery(char.docno):
                        continue
                    term = Term(prefix, ngram, char.start, char.end)
                    postings[char.docno].append(term)

    for i in postings.items():
        jobs.put(i)
    jobs.join()
log.info('<| complete')
