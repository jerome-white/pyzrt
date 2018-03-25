import linecache as lc
import multiprocessing as mp
from pathlib import Path
from argparse import ArgumentParser

import pyzrt as pz

def func(queue, nodes, dedups, output):
    log = pz.util.get_logger()

    while True:
        focus = queue.get()

        (document, *terms) = focus.strip().split()
        (document, *_) = Path(document).stem.split('.')

        log.info(document)

        with output.joinpath(document).open('w') as fp:
            for i in terms:
                (n, _) = i.split(':')
                offsets = lc.getline(dedups, int(n)).strip().split()
                for j in offsets:
                    (doc, *times) = lc.getline(nodes, int(j)).strip().split()
                    if doc == document:
                        print(n, *times, file=fp)

        queue.task_done()

arguments = ArgumentParser()
arguments.add_argument('--features', type=Path)
arguments.add_argument('--nodes', type=Path)
arguments.add_argument('--dedups', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--workers', type=int, default=mp.cpu_count())
args = arguments.parse_args()

queue = mp.JoinableQueue()
initargs = (
    queue,
    *map(str, (args.nodes, args.dedups)),
    args.output,
)
with mp.Pool(args.workers, func, initargs):
    with args.features.open() as fp:
        for i in fp:
            queue.put(i)
    queue.join()
