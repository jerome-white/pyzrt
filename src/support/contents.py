import csv
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

import pandas as pd

from zrtlib.indri import QueryDoc

class Entry:
    def __init__(self, query, entry, terms, description=None):
        self.query = query.stem
        self.topic = QueryDoc.components(Path(entry['query'])).topic
        self.model = entry['model']
        self.description = description

        self.terms = None if terms is None else len(pd.read_csv(terms))

    def __str__(self):
        components = [ self.description,
                       str(self.query),
                       self.terms,
                       self.topic,
                       self.model
        ]

        return ' '.join(map(str, components))

def func(args):
    (query, toc, root) = args

    # with toc.open() as fp:
    #     for (name, description) in csv.reader(fp):
    #         if name == family:
    #             self.ngrams = description
    #             break

    with query.open() as fp:
        terms = query.with_suffix('.terms')
        if not terms.exists():
            terms = None

        for line in csv.DictReader(fp):
            return Entry(query, line, terms)

arguments = ArgumentParser()
arguments.add_argument('--queries', type=Path)
arguments.add_argument('--toc', type=Path)
args = arguments.parse_args()

with Pool() as pool:
    f = lambda x: (x, args.toc, args.queries)
    for i in pool.imap_unordered(func, map(f, args.queries.glob('**/*.csv'))):
        print(i)
