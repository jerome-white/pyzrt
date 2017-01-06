import multiprocessing as mp

from pathlib import Path
from argparse import ArgumentParser

from zrtlib import zutils
from zrtlib import logger
from zrtlib.query import QueryBuilder

def func(args):
    (terms, model, output) = args
    
    log = logger.getlogger()
    log.info(terms.stem)

    with output.joinpath(terms.stem).open('w') as fp:
        q = QueryBuilder(model, terms)
        fp.write(str(q))
    
arguments = ArgumentParser()
arguments.add_argument('--model')
arguments.add_argument('--input', type=Path)
arguments.add_argument('--output', type=Path)
args = arguments.parse_args()

with mp.Pool() as pool:
    f = lambda x: (x, args.model.lower(), args.output)
    for _ in pool.imap(func, map(f, zutils.walk(args.input))):
        pass
