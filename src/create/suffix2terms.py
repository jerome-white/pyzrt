import csv
from pathlib import Path
from argparse import ArgumentParser
from collections import namedtuple
from multiprocessing import Pool

from zrtlib import logger
from zrtlib.corpus import Character

Term = namedtuple('Term', 'term, ngram, start, end')
Entry = namedtuple('Entry', 'docno, term')

class TermReader:
    def __init__(self, path, prefix, fill):
        self.path = path
        self.prefix = lambda x: prefix + str(x).zfill(fill)

    def __iter__(self):
        with self.path.open() as fp:
            reader = csv.reader(fp)
            for row in reader:
                p = self.prefix(reader.line_num)
                yield from map(lambda x: Entry(*x), self.parse(p, row))

    def parse(self, prefix, row):
        raise NotImplementedError()

    @staticmethod
    def builder(version, path, prefix='pt', fill=0):
        return [
            PythonTermReader,
            JavaTermReader,
        ][version](path, prefix, fill)

class PythonTermReader(TermReader):
    def parse(self, prefix, row):
        (ngram, *tokens) = row

        for i in tokens:
            toks = i.split()
            for j in range(0, len(toks), 3):
                char = Character.fromlist(toks[j:j+3])
                term = Term(prefix, ngram, char.start, char.end)

                yield (char.docno, term)

class JavaTermReader(TermReader):
    def parse(self, prefix, row):
        (docno, ngram, start) = row

        start = int(start)
        term = Term(prefix, ngram, start, start + len(ngram))

        yield (Path(docno), term)

def func(args):
    (document, fill, cli) = args

    with cli.output.joinpath(document.stem).open('w') as fp:
        writer = csv.DictWriter(fp, fieldnames=Term._fields)
        writer.writeheader()

        reader = TermReader.builder(cli.version,
                                    cli.suffix_tree,
                                    cli.term_prefix,
                                    fill)
        for entry in reader:
            if entry.docno == document:
                writer.writerow(entry.term._asdict())

    return document

arguments = ArgumentParser()
arguments.add_argument('--suffix-tree', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--term-prefix', default='pt')
arguments.add_argument('--version', type=int, default=1)
args = arguments.parse_args()

log = logger.getlogger(True)

log.info('>| begin')
with Pool() as pool:
    version = max(0, args.version - 1)
    reader = TermReader.builder(version, args.suffix_tree, args.term_prefix)

    terms = set()
    documents = set()
    for entry in reader:
        documents.add(entry.docno)
        terms.add(entry.term)
    digits = len(str(len(terms)))

    iterable = map(lambda x: (x, digits, args), documents)
    for i in pool.imap_unordered(func, iterable):
        log.info(i)
log.info('<| complete')
