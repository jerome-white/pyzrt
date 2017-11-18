import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile

import pyzrt as pz

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
    log = pz.util.get_logger()

    s = args.strainer.split(':') if args.strainer else None
    parser = pz.Parser(args.parser.lower(), pz.Strainer(s))
    recorder = Recorder(args.output, args.consolidate)

    while True:
        document = document_queue.get()
        log.info(document)

        for i in parser.parse(document):
            recorder.write(i.text, i.docno)

        document_queue.task_done()

arguments = ArgumentParser()
arguments.add_argument('--parser')
arguments.add_argument('--strainer')
arguments.add_argument('--documents', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
arguments.add_argument('--consolidate', action='store_true')
args = arguments.parse_args()

log = pz.util.get_logger(True)
log.info('>| begin')

document_queue = mp.JoinableQueue()
with mp.Pool(args.workers, func, (args, document_queue)):
    args.output.mkdir(parents=True, exist_ok=True)
    for i in pz.util.walk(args.documents):
        document_queue.put(i)
    document_queue.join()

log.info('<| complete')
