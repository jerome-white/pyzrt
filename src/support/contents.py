import csv
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

import pandas as pd

from zrtlib.indri import QueryDoc

class Entry:
    def __init__(self, query, line, toc, terms=None):
        self.query = query
        self.topic = QueryDoc.components(Path(line['query'])).topic
        self.model = line['model']

        self.ngrams = {
            '2017_0829': 'n-i',
            '2017_0905': 'n-0',
            '2017_0906': 'n-1',
            '2017_0924': 'TREC',
        }[self.query.parts[0]]

        if terms is not None:
            df = pd.read_csv(terms)
            self.terms = len(df)

    def __str__(self):
        components = [ self.ngrams,
                       str(self.query),
                       self.terms,
                       self.topic,
                       self.model
        ]

        return ' '.join(map(str, components))

def func(args):
    (query, toc, root) = args

    with query.open() as fp:
        for line in csv.DictReader(fp):
            path = query.relative_to(root).with_name(query.stem)
            terms = query.with_suffix('.terms')
            if not terms.exists():
                terms = None

            return Entry(path, line, toc, terms)

arguments = ArgumentParser()
arguments.add_argument('--queries', type=Path)
arguments.add_argument('--toc', type=Path)
args = arguments.parse_args()

with Pool() as pool:
    f = lambda x: (x, args.toc, args.queries)
    for i in pool.imap_unordered(func, map(f, args.queries.glob('**/*.csv'))):
        print(i)
