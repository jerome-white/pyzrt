import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser

import pyzrt as pz

def func(args):
    log = pz.util.get_logger(True)

    (document, model, output) = args
    log.info('{0} {1}'.format(document.stem, model))

    terms = pz.TermCollection(document)
    query = pz.Query(terms, model)
    output.write_text(str(query))

    return output.stem

def each(args):
    for model in args.model:
        for doc in pz.util.walk(args.term_files):
            if pz.TrecDocument.isquery(doc):
                out = args.output.joinpath(doc.stem).with_suffix('.' + model)
                if not out.exists():
                    yield (doc, model, out)

arguments = ArgumentParser()
arguments.add_argument('--term-files', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--model', action='append', default=['ua'])
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
args = arguments.parse_args()

log = pz.util.get_logger(True)

log.info('++ begin {0}'.format(args.term_files))
with mp.Pool(args.workers) as pool:
    for i in pool.imap_unordered(func, each(args)):
        log.info(i)
log.info('-- end')
