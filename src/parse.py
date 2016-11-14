import sys
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser

from zrtlib import logger
from zrtlib import zparser
from zrtlib import strainer

def directory_walker(path):
    for p in path.iterdir():
        if p.is_dir():
            yield from directory_walker(p)
        else:
            yield p

def f(args, document_queue):
    log = logger.getlogger()

    Parser = {
        'wsj': zparser.WSJParser,
        'test': zparser.TestParser,
        'pt': zparser.PseudoTermParser,
    }[args.archive_type.lower()]

    strain_selector = {
        'alpha': strainer.AlphaNumericStrainer,
        'trec': strainer.TRECStrainer,
    }

    s = strainer.Strainer()
    for i in args.strainer:
        Strainer = strain_selector[i]
        s = Strainer(s)
    parser = Parser(s)

    while True:
        document = document_queue.get()
        log.info(document)

        for i in parser.parse(document):
            p = args.corpus.joinpath(i.docno)
            with p.open('w') as fp:
                fp.write(i.text)

        document_queue.task_done()

arguments = ArgumentParser()
arguments.add_argument('--parser')
arguments.add_argument('--output-data', type=Path)
arguments.add_argument('--raw-data', type=Path)
arguments.add_argument('--strainer', action='append')
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
