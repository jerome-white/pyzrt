from pathlib import Path
from argparse import ArgumentParser

from gensim.models import Word2Vec

from zrtlib import logger
from zrtlib.terms import TermCollection

def sentences(corpus):
    log = logger.getlogger()

    for i in corpus.iterdir():
        log.debug(i.stem)

        terms = TermCollection(i)
        yield from map(str, terms.regions())

arguments = ArgumentParser()
arguments.add_argument('--corpus', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--workers', type=int)
args = arguments.parse_args()

# for i in enumerate(sentences(args.corpus)):
#     print(*i)

log = logger.getlogger()

log.info('BEGIN')
model = Word2Vec(sentences(args.corpus), workers=args.workers)
model.save(args.output)
log.info('END')
