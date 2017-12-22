from pathlib import Path
from argparse import ArgumentParser

import whoosh.index as wndx
from whoosh.qparser import QueryParser

import pyzrt as pz

arguments = ArgumentParser()
arguments.add_argument('--query', type=Path)
arguments.add_argument('--index', type=Path)
arguments.add_argument('--count', type=int, default=1000)
args = arguments.parse_args()

assert(args.index.is_dir())

log = pz.util.get_logger(True)

q = str(pz.TermCollection(args.query))
log.debug(q[:20])

log.info('|< BEGIN')
ix = wndx.open_dir(args.index)
# log.debug(ix.schema)

# with ix.searcher() as searcher:
#     query = QueryParser('content', ix.schema).parse(q)
#     results = searcher.search(query, limit=args.count)
#     for result in results:
#         doc = Path(result['document'])
#         print(doc.stem, result.score)

tc = pz.TermCollection(args.query)
qrels = [ None ] * args.count
search = pz.WhooshSearch(args.index, qrels)
for i in search.execute(repr(tc[0])):
    print(i)
log.info('|> COMPLETE')
