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

def func(args, document_queue):
    log = logger.getlogger()

    Parser = {
        'pt': zparser.PseudoTermParser,
        'wsj': zparser.WSJParser,
        'test': zparser.TestParser,
    }[args.parser.lower()]

    strain_selector = {
        'trec': strainer.TRECStrainer,
        'alpha': strainer.AlphaNumericStrainer,
    }

    s = strainer.Strainer()
    for i in args.strainer:
        Strainer = strain_selector[i.lower()]
        s = Strainer(s)
    parser = Parser(s)

    while True:
        document = document_queue.get()
        log.info(document)

        for i in parser.parse(document):
            p = args.output_data.joinpath(i.docno)
            with p.open('w') as fp:
                fp.write(i.text)

        document_queue.task_done()

arguments = ArgumentParser()
arguments.add_argument('--parser')
arguments.add_argument('--output-data', type=Path)
arguments.add_argument('--raw-data', type=Path)
arguments.add_argument('--strainer', action='append')
args = arguments.parse_args()

document_queue = mp.JoinableQueue()
with mp.Pool(initializer=func, initargs=(args, document_queue)):
    args.output_data.mkdir(parents=True, exist_ok=True)
    if args.raw_data:
        files = directory_walker(args.raw_data)
    else:
        files = map(lambda x: Path(x.strip()), sys.stdin)

    for i in files:
        document_queue.put(i)
    document_queue.join()
