from pathlib import Path
from argparse import ArgumentParser

from zrtlib.indri import QueryDoc

arguments = ArgumentParser()
arguments.add_argument('--query', type=Path)
args = arguments.parse_args()

qid = QueryDoc.components(args.query)
print(qid.topic)
