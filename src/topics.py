import gzip
from pathlib import Path
from argparse import ArgumentParser

from zrtlib import logger

arguments = ArgumentParser()
arguments.add_argument('--topics')
arguments.add_argument('--output', type=Path)
arguments.add_argument('--title', action='store_true')
arguments.add_argument('--description', action='store_true')
arguments.add_argument('--narrative', action='store_true')
args = arguments.parse_args()

log = logger.getlogger()

num = None
record = False
entry = []

with gzip.open(args.topics) as fp:
    for i in fp:
        line = i.decode().strip()
        if not line:
            continue

        parts = line.split()
        line_type = parts[0]
        if line_type == '<num>':
            if num is not None:
                log.info(num)
                path = args.output.joinpath(num)
                with path.open('w') as op:
                    print(' '.join(entry), file=op)
            num = parts[-1]
            entry = []
        elif line_type == '<title>' and args.title:
            start = 2 if parts[1] == 'Topic:' else 1
            entry.extend(parts[start:])
        elif line_type == '<desc>':
            record = args.description
        elif line_type == '<narr>':
            record = args.narrative
        elif line_type == '</top>':
            record = False
        elif record:
            entry.append(line)