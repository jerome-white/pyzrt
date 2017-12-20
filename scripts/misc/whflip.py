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

def func(args):
    (path, term) = args

    tc = pz.TermCollection(path)
    for i in range(len(tc)):
        encrypted = str(tc[i])
        if encrypted == term:
            tm = tc[i]
            unencrypted = repr(tm)
            tc[i] = pz.Term(unencrypted, unencrypted, tm.position)
    path.write_text(str(tc))

    return Entry(*map(str, (path, pz.TermCollection(path))))

def each(index, term):
    with index.reader() as reader:
        postings = reader.postings('contents', term)
        for i in postings.all_ids():
            fields = reader.stored_fields(i)
            yield (Path(fields['doc']), term)

def guesses(corpus):
    for doc in corpus.iterdir():
        yield from map(str, pz.TermCollection(doc))

arguments = ArgumentParser()
arguments.add_argument('--query', type=Path)
arguments.add_argument('--index', type=Path)
arguments.add_argument('--corpus', type=Path)
arguments.add_argument('--count', type=int, default=1000)
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
args = arguments.parse_args()

assert(args.index.is_dir())

log = pz.util.get_logger(True)

log.info('|< BEGIN')
with Pool(args.workers) as pool:
    definition = Entry(wfld.ID(stored=True, unique=True), wfld.TEXT)
    schema = wfld.Schema(**definition._asdict())
    ix = wndx.open_dir(args.index)
    writer = ix.writer(procs=args.workers, limitmb=args.memory)
    query = str(pz.TermDocument(args.query))

    for term in guesses(args.corpus):
        for i in pool.imap_unordered(func, each(ix, term)):
            writer.update_document(**i._asdict())

        with ix.searcher() as searcher:
            query = QueryParser('contents', ix.schema).parse(query)
            results = searcher.search(query, limit=args.count)
            for result in results:
                doc = Path(result['doc'])
                log.debug('{0} {1}'.format(doc, result.score))
log.info('|> COMPLETE')
