#
# Parses a directory of files into term collection files. If
# max-gram's are specified, then the set will be of variable length
# (between min-gram and max-gram); it will be of constant size
# otherwise.
#
# Generally, files are assumed to have already been parsed;
# specifically, they are not in the TREC format.
#

import string
import itertools as it
import multiprocessing as mp
import collections as cl
from pathlib import Path
from argparse import ArgumentParser

from zrtlib import logger
from zrtlib import zutils
from zrtlib.terms import Term, TermCollection

class FileParser:
    def __init__(self, document):
        self.document = document

    def __iter__(self):
        with self.document.open() as fp:
            for i in it.count():
                c = fp.read(1)
                if not c:
                    break
                yield from it.starmap(self.mkterm, self.get(c, i))

    def mkterm(self, chars, offset):
        ngram = ''.join(chars)
        return Term(ngram, ngram, offset - len(ngram))

    def get(self, character):
        raise NotImplementedError()

class WordParser(FileParser):
    def __init__(self, document):
        super().__init__(document)
        self.word = []

    def get(self, character, position):
        if character in string.whitespace:
            if self.word:
                yield (self.word, position)
                self.word.clear()
        else:
            self.word.append(character)

class NgramParser(FileParser):
    def __init__(self, document, minlen, maxlen=None):
        super().__init__(document)

        self.minlen = minlen
        if maxlen is None:
            maxlen = self.minlen
        assert(0 < self.minlen <= maxlen)

        self.window = cl.deque(maxlen=maxlen)

    def get(self, character, position):
        if character in string.whitespace:
            character = '_'

        self.window.append(character)

        if len(self.window) == self.window.maxlen:
            for i in range(self.minlen, self.window.maxlen + 1):
                for j in range(self.window.maxlen - i + 1):
                    chars = it.islice(self.window, j, j + i)
                    yield (chars, position + 1)

def func(args):
    (document, output_directory, minlen, maxlen) = args

    log = logger.getlogger()
    log.info(document.stem)

    collection = TermCollection()
    if minlen is None:
        parser = WordParser(document)
    else:
        parser = NgramParser(document, minlen, maxlen)
    collection.extend(parser)

    if collection:
        o = output_directory.joinpath(document.stem)
        with o.open('w') as fp:
            collection.tocsv(fp)
    else:
        log.warning(document.stem)

arguments = ArgumentParser()
arguments.add_argument('--documents', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--min-gram', type=int)
arguments.add_argument('--max-gram', type=int)
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
args = arguments.parse_args()

log = logger.getlogger(True)

log.info('>| begin')
with mp.Pool(args.workers) as pool:
    f = lambda x: (x, args.output, args.min_gram, args.max_gram)
    for _ in pool.imap_unordered(func, map(f, zutils.walk(args.documents))):
        pass
log.info('<| complete')
