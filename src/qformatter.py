import operator as op
import xml.etree.ElementTree as et
from pathlib import Path
from argparse import ArgumentParser

class Query:
    def __init__(self, path):
        self.name = path.stem.zfill(3)
        self.xml = et.Element('DOC')

    def __len__(self):
        return len(self.xml.findall('DOCNO'))

    def __str__(self):
        return et.tostring(self.xml, encoding="unicode")

    def add(self, query):
        docno = et.SubElement(self.xml, 'DOCNO')
        docno.text = 'WSJQ00{0}-{1:04d}'.format(self.name, len(self))

        text = et.SubElement(self.xml, 'TEXT')
        text.text = ' '.join(query)

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
            fp.write(str(query))
