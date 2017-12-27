import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

import whoosh.index as wndx

import pyzrt as pz

arguments = ArgumentParser()
arguments.add_argument('--corpus', type=Path)
arguments.add_argument('--index', type=Path)
arguments.add_argument('--memory', type=int, default=128)
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
args = arguments.parse_args()

assert(not args.index.exists())

log = pz.util.get_logger(True)

log.info('|< BEGIN')
with Pool(args.workers) as pool:
    args.index.mkdir()
    ix = wndx.create_in(args.index, pz.WhooshSchema())
    # stem_ana = ix.schema['content'].format.analyzer
    # stem_ana.cachesize = -1
    # stem_ana.clear()

    with ix.writer(procs=args.workers, limitmb=args.memory) as writer:
        iterable = pz.util.walk(args.corpus)
        for i in pool.imap_unordered(pz.WhooshEntry, iterable):
            log.debug(i.document)
            writer.add_document(**i._asdict())
        log.info('|+ COMMIT')
log.info('|> COMPLETE')
