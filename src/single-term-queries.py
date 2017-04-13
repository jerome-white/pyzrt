from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

from zrtlib import zutils
from zrtlib import logger
from zrtlib.query import QueryBuilder
from zrtlib.document import TermDocument, HiddenDocument

def func(args):
    (terms, options) = args

    log = logger.getlogger()
    log.info(terms.stem)

    writer = None    
    document = TermDocument(terms)

    with options.output.joinpath(terms.stem).open('w') as fp:
        with QueryExecutor(options.index, options.qrels) as engine:
            for i in document.df['term'].unique():
                query = HiddenDocument(terms)        
                query.flip(tr)
                
                engine.query(QueryBuilder(options.model, query))
                results = {
                    'term': i,
                    **next(engine.evaluate()),
                }
                
                if writer is None:
                    writer = csv.DictWriter(fp, fieldnames=results.keys())
                    writer.writeheader()
                writer.writerow(results)

arguments = ArgumentParser()
arguments.add_argument('--model')
arguments.add_argument('--index', type=Path)
arguments.add_argument('--qrels', type=Path)
arguments.add_argument('--input', type=Path)
arguments.add_argument('--output', type=Path)
args = arguments.parse_args()

log = logger.getlogger()

with Pool() as pool:
    mkargs = lambda x: (x, args)
    for i in pool.imap(func, map(mkargs, zutils.walk(args.input))):
        log.info(i.stem)
