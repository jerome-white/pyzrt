import csv
from collections import namedtuple

import pandas as pd

class PseudoTermWriter:
    def __init__(self, suffix, prefix='pt'):
        self.suffix = suffix
        self.ngrams = len(str(len(self.suffix)))
        self.prefix = prefix

    #
    # Create (pseudo)terms
    #
    def write(self, path):
        fieldnames = [ 'term', 'ngram', 'start', 'end' ]

        for (i, (ngram, collection)) in enumerate(self.suffix.each()):
            pt = self.prefix + str(i).zfill(self.ngrams)
            for token in collection:
                for t in token:
                    row = dict(zip(fieldnames, [ pt, ngram, t.start, t.end ]))

                    p = path.joinpath(t.docno.stem)
                    with p.open('a') as fp:
                        writer = csv.DictWriter(fp, fieldnames=fieldnames)
                        if fp.tell() == 0:
                            writer.writeheader()
                        writer.writerow(row)

    #
    # Build (pseudo)term files that are capable of indexing
    #
    def consolidate(self, source, destination):
        for i in source.iterdir():
            path_or_buf = str(destination.joinpath(i.stem))
            
            df = pd.read_csv(str(i))
            df.sort_values(by=[ 'start', 'end' ], inplace=True)

            df.to_csv(columns=[ 'term' ],
                      header=False,
                      index=False,
                      line_terminator=' ',
                      path_or_buf=path_or_buf,
                      sep=' ')
