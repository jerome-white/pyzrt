from pathlib import Path
from argparse import ArgumentParser

from zrtlib import zparser

parsers = {
    'WSJ': zparser.WSJParser,
    'test': zparser.TestParser,
}

arguments = ArgumentParser()
arguments.add_argument('--archive-type')
arguments.add_argument('--corpus', type=Path)
args = arguments.parse_args()

args.corpus.mkdir(parents=True, exist_ok=True)
strainer = zparser.AlphaNumericStrainer()
parser = parsers[args.archive_type](strainer)

for (i, data) in parser:
    p = args.corpus.joinpath(i)
    assert(not p.exists())
    with p.open('w') as fp:
        fp.write(data)
