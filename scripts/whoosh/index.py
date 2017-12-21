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

log = pz.util.get_logger(True)

log.info('|< BEGIN')
with Pool(args.workers) as pool:
    if args.index.exists():
        ix = wndx.open_dir(args.index)
    else:
        ix = wndx.create_in(args.index, pz.WhooshEntry())
    writer = ix.writer(procs=args.workers,
                       limitmb=args.memory,
                       multisegment=True)
    for i in pool.imap_unordered(pz.WhooshEntr, pz.util.walk(args.corpus)):
        log.debug(i.document)
        writer.add_document(**i._asdict())
    writer.commit()
log.info('|> COMPLETE')
