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

    q = query.pop() if query else QueryBuilder(model, TermDocument(terms))
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
        document.flip()
        query = QueryBuilder(model, document)
        indri.add(query.compose())

    return instantaneous(args + (indri, ))

arguments = ArgumentParser()
arguments.add_argument('--model')
arguments.add_argument('--input', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--progressive', action='store_true')
args = arguments.parse_args()

log = logger.getlogger()

with Pool() as pool:
    func = progressive if args.progressive else instantaneous
    mkargs = lambda x: (x, args.model.lower(), args.output)
    for i in pool.imap(func, map(mkargs, zutils.walk(args.input))):
        log.info(i.stem)
