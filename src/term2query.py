import csv
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

from zrtlib import zutils
from zrtlib import logger
from zrtlib.indri import IndriQuery
from zrtlib.query import QueryBuilder
from zrtlib.document import TermDocument, HiddenDocument

def instantaneous(args):
    (terms, model, output, *query) = args

    q = query.pop() if query else QueryBuilder(TermDocument(terms), model)
    with output.joinpath(terms.stem).open('w') as fp:
        print(q, file=fp)

    return terms

def progressive(args):
    (terms, model, output) = args

    log = logger.getlogger()
    log.info(terms.stem)

    indri = IndriQuery()
    document = HiddenDocument(terms)

    while document:
        flipped = document.flip()
        assert(flipped > 0)
        query = QueryBuilder(document, model)
        indri.add(query.compose())

    return instantaneous(args + (indri, ))

arguments = ArgumentParser()
arguments.add_argument('--model')
arguments.add_argument('--action')
arguments.add_argument('--input', type=Path)
arguments.add_argument('--output', type=Path)
args = arguments.parse_args()

log = logger.getlogger()
registry = { i.__name__: i for i in (instantaneous, progressive, single) }

with Pool() as pool:
    f = registry[args.action]
    mkargs = lambda x: (x, args.model.lower(), args.output)
    for i in pool.imap(f, map(mkargs, zutils.walk(args.input))):
        log.info(i.stem)
