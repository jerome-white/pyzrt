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

    document = TermDocument(terms)

    for i in document.df['term'].unique():
        doc = HiddenDocument(terms)
        doc.flip(i)

        query = QueryBuilder(options.model, doc)
        indri.add(query.compose())

    with options.output.joinpath(terms.stem).open('w') as fp:
        with QueryExecutor(options.index, options.qrels) as engine:
            engine.query(indri)
            writer = None

            for (run, results) in engine.evaluate():
                assert('run' not in results)
                row = { 'run': run, **results }

                if writer is None:
                    writer = csv.DictWriter(fp, fieldnames=row.keys())
                    writer.writeheader()
                writer.writerow(row)

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
