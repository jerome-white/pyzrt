import multiprocessing as mp

from pathlib import Path
from argparse import ArgumentParser

from zrtlib import zutils
from zrtlib import logger
from zrtlib.indri import QueryDoc
from zrtlib.query import QueryBuilder
from zrtlib.document import TermDocument

def func(args):
    (terms, model, output) = args
    
    query = str(QueryBuilder(model, TermDocument(terms)))
    with output.joinpath(terms.stem).open('w') as fp:
        fp.write(query)

    return terms

arguments = ArgumentParser()
arguments.add_argument('--model')
arguments.add_argument('--input', type=Path)
arguments.add_argument('--output', type=Path)
args = arguments.parse_args()

log = logger.getlogger()

with mp.Pool() as pool:
    f = lambda x: (x, args.model.lower(), args.output)
    for i in pool.imap(func, map(f, zutils.walk(args.input))):
        qid = QueryDoc(i)
        log.info(qid.topic)
