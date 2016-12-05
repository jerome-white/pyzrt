import sys
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile

from zrtlib import logger
from zrtlib import zparser
from zrtlib import strainer

class Recorder:
    def __init__(self, path, single_file):
        self.path = path
        self.single_file = single_file

        if self.single_file:
            directory = str(self.path)
            self.fp = NamedTemporaryFile(mode='w', dir=directory, delete=False)
        else:
            self.fp = None

    def write(self, data, location):
        if self.single_file:
            path = self.path.joinpath(location)
            fp = path.open('w')
        else:
            fp = self.fp

        fp.write(data)

        if self.single_file:
            fp.close()

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

    recorder = Recorder(args.output_data, args.consolidate)

    while True:
        document = document_queue.get()
        log.info(document)

        for i in parser.parse(document):
            recorder.write(i.text, i.docno)

        document_queue.task_done()

arguments = ArgumentParser()
arguments.add_argument('--parser')
arguments.add_argument('--output-data', type=Path)
arguments.add_argument('--raw-data', type=Path)
arguments.add_argument('--strainer', action='append')
arguments.add_argument('--consolidate', action='store_true')
args = arguments.parse_args()

log = logger.getlogger(True)
log.info('>| begin')

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

log.info('<| complete')
