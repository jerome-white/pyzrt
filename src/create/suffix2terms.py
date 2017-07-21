import csv
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from collections import namedtuple, defaultdict

from zrtlib import logger
from zrtlib.corpus import Character

Term = namedtuple('Term', 'term, ngram, start, end')

class TermReader:
    def __init__(self, path, prefix):
        self.postings = defaultdict(list)

        with path.open() as fp:
            # count the number of terms
            for (i, _) in enumerate(fp):
                pass
            log.info('terms {0}'.format(i))
            digits = len(str(i))
            fp.seek(0)

            # read each term
            reader = csv.reader(fp)
            for row in reader:
                p = prefix + str(reader.line_num).zfill(digits)
                for (docno, term) in self.parse(p, row):
                    self.postings[docno].append(term)

    def parse(self, prefix, row):
        raise NotImplementedError()

class PythonTermReader:
    def parse(self, prefix, row):
        (ngram, *tokens) = row

        for i in tokens:
            toks = i.split()
            for j in range(0, len(toks), 3):
                char = Character.fromlist(toks[j:j+3])
                term = Term(prefix, ngram, char.start, char.end)

                yield (char.docno, term)

class JavaTermReader:
    def parse(self, prefix, row):
        (docno, ngram, start) = row

        term = Term(prefix, ngram, start, start + len(ngram))

        yield (docno, term)

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
arguments.add_argument('--version', type=int, default=0)
args = arguments.parse_args()

log = logger.getlogger(True)
jobs = mp.JoinableQueue()

log.info('>| begin')
with mp.Pool(initializer=func, initargs=(jobs, args.output)):
    terms = [
        PythonTermReader,
        JavaTermReader,
        ][args.version](args.suffix_tree, args.term_prefix)

    for i in terms.postings.items():
        jobs.put(i)
    jobs.join()
log.info('<| complete')
