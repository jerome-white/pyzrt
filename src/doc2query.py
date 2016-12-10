import multiprocessing as mp
import xml.etree.ElementTree as et
from pathlib import Path
from argparse import ArgumentParser
from collections import defaultdict, namedtuple

from zrtlib import logger
from zrtlib import zutils
from zrtlib.query import QueryDoc
from zrtlib.zparser import WSJParser
from zrtlib.strainer import Strainer, AlphaNumericStrainer

class QuerySet:
    def __init__(self, topic, documents, output):
        self.documents = documents
        self.output = output.joinpath(topic)

def mkelement(name, parent=None, text='\n', tail='\n'):
    if parent is None:
        element = et.Element(name)
    else:
        element = et.SubElement(parent, name)
    element.text = text
    element.tail = tail

    return element

def func(qset):
    log = logger.getlogger()

    keys = [ 'type', 'number', 'text' ]
    parser = WSJParser(AlphaNumericStrainer(Strainer()))
    query = mkelement('parameter')

    for (i, document) in enumerate(qset.documents):
        log.info(document.stem)
        for j in parser.parse(document):
            q = mkelement('query', query)
            for (x, y) in zip(keys, ('indri', str(i), j.text)):
                mkelement(x, q, y)

    with qset.output.open('w') as fp:
        fp.write(et.tostring(query, encoding='unicode'))

arguments = ArgumentParser()
arguments.add_argument('--input', type=Path)
arguments.add_argument('--output', type=Path)
args = arguments.parse_args()

with mp.Pool() as pool:
    d = defaultdict(list)
    for document in zutils.walk(args.input):
        query = QueryDoc.components(document)
        d[query.topic].append(document)

    f = lambda x: QuerySet(*x, args.output)
    for _ in pool.imap(func, map(f, d.items())):
        pass
