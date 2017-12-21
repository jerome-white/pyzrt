import collections as clc
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

import whoosh.fields as wfld
import whoosh.index as wndx
from whoosh.qparser import QueryParser

import pyzrt as pz

Entry = clc.namedtuple('Entry', 'doc, contents')

arguments = ArgumentParser()
arguments.add_argument('--query', type=Path)
arguments.add_argument('--index', type=Path)
arguments.add_argument('--count', type=int, default=1000)
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
args = arguments.parse_args()

assert(args.index.is_dir())

log = pz.util.get_logger(True)

log.info('|< BEGIN')
with Pool(args.workers) as pool:
    definition = Entry(wfld.ID(stored=True), wfld.TEXT)
    schema = wfld.Schema(**definition._asdict())

    ix = wndx.open_dir(args.index)

    term = 'pt00033443'
    with ix.reader() as reader:
        postings = reader.postings('contents', term)
        for i in postings.all_ids():
            fields = reader.stored_fields(i)
            print(fields)

    with ix.searcher() as searcher:
        query = QueryParser('contents', ix.schema).parse(term)
        results = searcher.search(query, limit=args.count)
        for result in results:
            doc = Path(result['doc'])
            log.debug('{0} {1}'.format(doc, result.score))
log.info('|> COMPLETE')
