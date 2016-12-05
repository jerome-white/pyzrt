#
# Formats a raw query (data/query) into the DOC/DOCNO/TEXT format
# required for TREC (and ultimately) for the parser.
#

import xml.etree.ElementTree as et
from pathlib import Path
from argparse import ArgumentParser

from zrtlib.query import QueryDoc

arguments = ArgumentParser()
arguments.add_argument('--input', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--include-topic', action='store_true')
args = arguments.parse_args()

for i in args.input.iterdir():
    if not i.stem.isdigit():
        continue

    qdocs = QueryDoc(i)
    with i.open() as fp:
        q = []
        topic = args.include_topic
        for j in fp:
            line = j.strip()
            if line:
                q.append(line)
            else:
                if topic:
                    qdocs.add(q)
                q = []
                topic = True

        if q and topic:
            qdocs.add(q)

    if qdocs:
        output = args.output.joinpath('WSJ_Q' + i.stem)
        with output.open('w') as fp:
            for j in qdocs:
                fp.write(j)
