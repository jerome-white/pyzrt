from pathlib import Path
from argparse import ArgumentParser

from zrtlib import corpus

parsers = {
    'WSJ': corpus.WSJParser,
    'test': corpus.TestParser,
}

arguments = ArgumentParser()
arguments.add_argument('--archive-type')
arguments.add_argument('--corpus', type=Path)
args = arguments.parse_args()

args.output_directory.mkdir(parents=True, exist_ok=True)
parser = parsers[args.archive_type]()

for (i, data) in parser.parse():
    p = args.output_directory.joinpath(i)
    with p.open('w') as fp:
        fp.write(data)
