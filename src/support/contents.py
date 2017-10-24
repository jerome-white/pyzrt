import csv
import pandas as pd
from pathlib import Path
from multiprocessing import Pool

from zrtlib.indri import QueryDoc

class Entry:
    def __init__(self, path, line):
        self.path = path.relative_to('data/models').with_name(path.stem)
        self.topic = QueryDoc.components(Path(line['query'])).topic
        self.model = line['model']

        self.ngrams = {
            '2017_0829': 'n-i',
            '2017_0905': 'n-0',
            '2017_0906': 'n-1',
            '2017_0924': 'TREC',
        }[self.path.parts[0]]

        terms = path.with_suffix('.terms')
        if terms.exists():
            df = pd.read_csv(terms)
            self.terms = len(df)
        else:
            self.terms = None

    def __str__(self):
        components = [ self.ngrams,
                       *self.path.parts,
                       self.topic,
                       self.model
        ]
        if self.terms:
            components.append(self.terms)
        
        return ','.join(map(str, components))

def func(args):
    with args.open() as fp:
        reader = csv.DictReader(fp)
        for line in reader:
            return Entry(args, line)

with Pool() as pool:
    path = Path('data/models')
    for i in pool.imap_unordered(func, path.glob('**/*.csv')):
        print(i)
