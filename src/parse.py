import parser

from pathlib import Path
from argparse import ArgumentParser

parsers = {
    'WSJ': parser.WSJParser,
    'test': parser.TestParser,
    }

arguments = ArgumentParser()
arguments.add_argument('--archive-type')
arguments.add_argument('--output-directory')
args = arguments.parse_args()
assert(args.archive_type in parsers)

path = Path(args.output_directory)
parser = parsers[args.archive_type]()

for (i, data) in parser.parse():
    p = path.joinpath(i)
    with p.open('w') as fp:
        fp.write(data)
