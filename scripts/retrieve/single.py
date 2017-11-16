import os
import csv
import collections as cl
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile

from pyzrt import zutils
from pyzrt import logger
from pyzrt.retrieval.query import Query
from pyzrt.retrieval.indri import QueryDoc
from pyzrt.types.terms import Term, TermCollection

def func(args):
    log = logger.getlogger()

    (document, model, output) = args
    log.info('{0} {1}'.format(document.stem, model))

    terms = TermCollection(document)
    query = Query.builder(document, model)
    output.write_text(str(query))

    return output.stem

def each(args):
    for model in args.models:
        for document in zutils.walk(args.term_files):
            if QueryDoc.isquery(document):
                out = output.joinpath(document.stem).with_suffix('.' + model)
                if not out.exists():
                    yield (document, model, out)

arguments = ArgumentParser()
arguments.add_argument('--term-files', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--model', action='append', default=['baseline'])
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
args = arguments.parse_args()

log = logger.getlogger(True)

log.info('++ begin {0}'.format(args.term_files))
with mp.Pool(args.workers) as pool:
    for i in pool.imap_unordered(func, each(args)):
        log.info(i)
log.info('-- end')
