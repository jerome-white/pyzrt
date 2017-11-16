import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser

from gensim.models import Word2Vec

from zrtlib import logger
from zrtlib.terms import TermCollection

class PseudoTermCorpus:
    def __init__(self, corpus):
        self.corpus = corpus

    def __iter__(self):
        self.iterdir = self.corpus.iterdir()
        self.regions = None

        return self

    def __next__(self):
        while True:
            if self.regions is None:
                tc = TermCollection(next(self.iterdir))
                self.regions = tc.regions()
            try:
                return list(map(str, next(self.regions)))
            except StopIteration:
                self.regions = None

arguments = ArgumentParser()
arguments.add_argument('--corpus', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
args = arguments.parse_args()

log = logger.getlogger()

# for i in enumerate(PseudoTermCorpus(args.corpus)):
#     log.info('{0}: {1}'.format(*i))

log.info('BEGIN')
model = Word2Vec(PseudoTermCorpus(args.corpus), workers=args.workers)
model.save(str(args.output))
log.info('END')
