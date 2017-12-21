import collections as clc
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

from whoosh import fields as w_fields
from whoosh import index as w_index

import pyzrt as pz

Entry = clc.namedtuple('Entry', 'doc, contents')

def func(path):
    log = pz.util.get_logger()
    log.info(path.stem)
    
    return Entry(*map(str, (path, pz.TermCollection(path))))

arguments = ArgumentParser()
arguments.add_argument('--corpus', type=Path)
arguments.add_argument('--index', type=Path)
arguments.add_argument('--memory', type=int, default=128)
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
args = arguments.parse_args()

assert(args.index.is_dir())

log = pz.util.get_logger(True)

log.info('|< BEGIN')
with Pool(args.workers) as pool:
    definition = Entry(w_fields.ID(stored=True), w_fields.TEXT)
    schema = w_fields.Schema(**definition._asdict())
    ix = w_index.create_in(args.index, schema)
    ix = w_index.open_dir(args.index)
    writer = ix.writer(procs=args.workers,
                       limitmb=args.memory,
                       multisegment=True)
    for i in pool.imap_unordered(func, pz.util.walk(args.corpus)):
        writer.add_document(**i._asdict())
    writer.commit()
log.info('|> COMPLETE')
