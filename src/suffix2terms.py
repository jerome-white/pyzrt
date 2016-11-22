import csv
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from collections import namedtuple, defaultdict

from zrtlib import logger
from zrtlib.corpus import Character

Term = namedtuple('Term', 'term, ngram, start, end')

def f(jobs, path):
    log = logger.getlogger()

    while True:
        (document, terms) = jobs.get()
        log.info('{0} |{1}|'.format(document, len(terms)))

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
args = arguments.parse_args()

log = logger.getlogger(True)
jobs = mp.JoinableQueue()

with mp.Pool(initializer=f, initargs=(jobs, args.output)):
    postings = defaultdict(list)
    with args.suffix_tree.open() as fp:
        terms = sum([ 1 for _ in fp ])
        log.info('terms {0}'.format(terms))
        digits = len(str(terms)))

        fp.seek(0)
        reader = csv.reader(fp)

        for (i, (ngram, *tokens)) in enumerate(reader):
            pt = args.term_prefix + str(i).zfill(digits)
            for j in tokens:
                c = Character.fromlist(j.split())
                term = Term(pt, ngram, c.start, c.end)
                postings[c.docno].append(term)

    for i in postings.items():
        jobs.put(i)
    jobs.join()
