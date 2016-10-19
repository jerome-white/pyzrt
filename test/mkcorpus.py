import random
from pathlib import Path
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile

from zrtlib import logger

arguments = ArgumentParser()
arguments.add_argument('--directory')
arguments.add_argument('--files', type=int, default=1)
arguments.add_argument('--size', type=int, default=1)
args = arguments.parse_args()

log = logger.getlogger()

for _ in range(args.files):
    with NamedTemporaryFile(mode='w', dir=args.directory, delete=False) as fp:
        log.info(fp.name)
        for _ in range(args.size):
            c = chr(random.randint(ord('a'), ord('z')))
            fp.write(c)
