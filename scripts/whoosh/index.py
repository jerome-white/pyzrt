import math
import collections as cl
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser

import whoosh.index as wndx
from whoosh.reading import SegmentReader

import pyzrt as pz

class Fibonacci:
    def __init__(self):
        self.five = math.sqrt(5)
        self.golden = (1 + self.five) / 2

    def __call__(self, n):
        return int((self.golden ** n - (-self.golden) ** -n) / self.five)

def merge_small_(writer, segments):
    log = pz.util.get_logger()
    log.debug('segments {0}'.format(len(segments)))

    segs = cl.defaultdict(list)
    for i in segments:
        size = i.doc_count_all()
        segs[count].append(i)

    docs = 0
    pivot = False
    merge = []
    fib = Fibonacci()
    for (i, s) in enumerate(sorted(segs.keys())):
        docs += s
        ptr = segs[s]
        while ptr:
            merge.append(ptr.pop())
            if i > 3 and docs < fib(i + 5):
                pivot = True
                break
        if pivot:
            break
    log.debug('merged {0}'.format(len(merge)))

    for i in merge:
        with SegmentReader(writer.storage, writer.schema, i) as reader:
            writer.add_reader(reader)

    remain = []
    for i in segs.values():
        remain.extend(i)
    log.debug('remain {0}'.format(len(remain)))

    return remain

arguments = ArgumentParser()
arguments.add_argument('--corpus', type=Path)
arguments.add_argument('--index', type=Path)
arguments.add_argument('--memory', type=int, default=128)
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
args = arguments.parse_args()

assert(not args.index.exists())

log = pz.util.get_logger(True)

log.info('|< BEGIN')
with mp.Pool(args.workers) as pool:
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
        # writer.mergetype = merge_small_
        log.info('|+ COMMIT')
log.info('|> COMPLETE')
