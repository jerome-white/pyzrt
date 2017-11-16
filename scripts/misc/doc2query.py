import multiprocessing as mp

from pathlib import Path
from argparse import ArgumentParser
from collections import defaultdict, namedtuple

from zrtlib import logger
from zrtlib import zutils
from zrtlib.indri import IndriQuery, QueryDoc
from zrtlib.zparser import WSJParser
from zrtlib.strainer import Strainer, AlphaNumericStrainer

class QuerySet:
    def __init__(self, topic, documents, output):
        self.documents = documents
        self.output = output.joinpath(topic)

def func(qset):
    log = logger.getlogger()

    parser = WSJParser(AlphaNumericStrainer(Strainer()))
    query = IndriQuery()

    for (i, document) in enumerate(qset.documents):
        log.info(document.stem)
        for j in parser.parse(document):
            query.add(j.text)

    with qset.output.open('w') as fp:
        fp.write(str(query))

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
