from pathlib import Path
from argparse import ArgumentParser

import whoosh.index as wndx
import whoosh.scoring as wscr
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

tc = pz.TermCollection(args.query)
qrels = [ None ] * args.count
search = pz.WhooshSearch(args.index, qrels)

query = tc
# query = repr(tc[0])
# query = ' '.join(map(repr, tc[:3]))

for i in search.execute(query):
    print(i)
log.info('|> COMPLETE')
