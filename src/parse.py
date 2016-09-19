from pathlib import Path
from argparse import ArgumentParser

import parser

parsers = {
    'WSJ': parser.WSJParser,
    'test': parser.TestParser,
}

arguments = ArgumentParser()
arguments.add_argument('--archive-type')
arguments.add_argument('--output-directory', type=Path)
args = arguments.parse_args()
exit()
path = Path(args.output_directory)
path.mkdir(parents=True, exists_ok=True)

parser = parsers[args.archive_type]()

for (i, data) in parser.parse():
    p = path.joinpath(i)
    with p.open('w') as fp:
        fp.write(data)
