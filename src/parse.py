import sys
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile

from zrtlib import logger
from zrtlib import zutils
from zrtlib import zparser
from zrtlib import strainer

class Recorder:
    def __init__(self, path, single_file):
        self.path = path

        if single_file:
            directory = str(self.path)
            self.fp = NamedTemporaryFile(mode='w', dir=directory, delete=False)
        else:
            self.fp = None

    def write(self, data, location):
        single_use = not self.fp or self.fp.closed
        if single_use:
            path = self.path.joinpath(location)
            self.fp = path.open('w')

        self.fp.write(data)
        self.fp.flush()

        if single_use:
            self.fp.close()

def func(args, document_queue):
    log = logger.getlogger()

    Parser = {
        'pt': zparser.PseudoTermParser,
        'wsj': zparser.WSJParser,
        'test': zparser.TestParser,
    }[args.parser.lower()]

    parser = Parser(strainer.builder(args.strainer))

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

    for i in zutils.walk(args.raw_data):
        document_queue.put(i)
    document_queue.join()

log.info('<| complete')
