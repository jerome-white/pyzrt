import sys
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser

from zrtlib import logger
from zrtlib import zparser

def directory_walker(path):
    for p in path.iterdir():
        if p.is_dir():
            yield from directory_walker(p)
        else:
            yield p

def f(args, document_queue):
    Parser = {
        'wsj': zparser.WSJParser,
        'test': zparser.TestParser,
    }[args.archive_type.lower()]

    strainer = zparser.AlphaNumericStrainer() if args.strain else None
    parser = Parser(strainer)

    log = logger.getlogger()

    while True:
        document = document_queue.get()
        log.info(document)

        for (i, data) in parser.parse(document):
            p = args.corpus.joinpath(i)
            assert(not p.exists())
            with p.open('w') as fp:
                fp.write(data)

        document_queue.task_done()

arguments = ArgumentParser()
arguments.add_argument('--archive-type')
arguments.add_argument('--corpus', type=Path)
arguments.add_argument('--raw-data', type=Path)
arguments.add_argument('--strain', action='store_true')
args = arguments.parse_args()

args.corpus.mkdir(parents=True, exist_ok=True)

document_queue = mp.JoinableQueue()
with mp.Pool(initializer=f, initargs=(args, document_queue)):
    if args.raw_data:
        files = directory_walker(args.raw_data)
    else:
        files = map(lambda x: Path(x.strip()), sys.stdin)

    for i in files:
        document_queue.put(i)
    document_queue.join()
