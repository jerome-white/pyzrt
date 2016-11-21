import operator as op
import xml.etree.ElementTree as et
from pathlib import Path
from argparse import ArgumentParser

class QueryDocs:
    def __init__(self, path):
        self.name = path.stem.zfill(3)
        self.docs = []

    def __iter__(self):
        yield from map(lambda x: et.tostring(x, encoding="unicode"), self.docs)

    def __bool__(self):
        return len(self.docs) > 0

    def add(self, query):
        doc = et.Element('DOC')

        docno = et.SubElement(doc, 'DOCNO')
        docno.text = 'WSJQ00{0}-{1:04d}'.format(self.name, len(self.docs))

        text = et.SubElement(doc, 'TEXT')
        text.text = ' '.join(query)

        self.docs.append(doc)

arguments = ArgumentParser()
arguments.add_argument('--input', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--include-topic', action='store_true')
args = arguments.parse_args()

for i in filter(lambda x: x.stem.isdigit(), args.input.iterdir()):
    qdocs = QueryDocs(i)
    with i.open() as fp:
        q = []
        topic = args.include_topic
        for line in map(op.methodcaller('strip'), fp):
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
