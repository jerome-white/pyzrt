import operator as op
import xml.etree.ElementTree as et
from pathlib import Path
from argparse import ArgumentParser

class Query(list):
    def __init__(self, path):
        self.name = path.stem.zfill(3)

    def each(self):
        for i in self:
            yield et.tostring(i, encoding="unicode")

    def add(self, query):
        doc = et.Element('DOC')

        docno = et.SubElement(doc, 'DOCNO')
        docno.text = 'WSJQ00{0}-{1:04d}'.format(self.name, len(self))

        text = et.SubElement(doc, 'TEXT')
        text.text = ' '.join(query)

        self.append(doc)

arguments = ArgumentParser()
arguments.add_argument('--input', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--include-topic', action='store_true')
args = arguments.parse_args()

for i in filter(lambda x: x.stem.isdigit(), args.input.iterdir()):
    query = Query(i)
    with i.open() as fp:
        q = []
        topic = args.include_topic
        for line in map(op.methodcaller('strip'), fp):
            if line:
                q.append(line)
            else:
                if topic:
                    query.add(q)
                q = []
                topic = True

        if q and topic:
            query.add(q)

    if len(query) > 0:
        output = args.output.joinpath('WSJ_Q' + i.stem)
        with output.open('w') as fp:
            for j in query.each():
                fp.write(j)
