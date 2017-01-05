from collections import namedtuple

import pandas as pd

Region = namedtuple('Region', 'n, first, last, df')

class TermDocument:
    def __init__(self, document, include_lengths=False):
        self.df = pd.read_csv(document)
        self.df.sort_values(by=[ 'start', 'end' ], inplace=True)

        if include_lengths:
            self.df['length'] = self.df['end'] - self.df['start']

        region = 0
        updates = {}
        last = None

        self.df['region'] = region
        for row in self.df.itertuples():
            if last is not None:
                region += row.start > last.end
                updates[row.Index] = region
            last = row
        groups = pd.DataFrame(list(updates.values()),
                              index=updates.keys(),
                              columns=[ 'region' ])
        self.df.update(groups)

    def __str__(self):
        return self.df.to_csv(columns=[ 'term' ],
                              header=False,
                              index=False,
                              line_terminator=' ',
                              sep=' ')
        
    def regions(self):
        groups = self.df.groupby(by=['region'], sort=False)
        n = groups.size().count() - 1

        for (i, (j, df)) in enumerate(groups):
            yield Region(j, i == 0, i == n, df)

class HiddenDocument(TermDocument):
    def __init__(self, document, include_lengths=False):
        super().__init__(document, include_lengths)

        term = 'pt'
        self.df.rename(columns={ 'term': term }, inplace=True)
        self.df['term'] = self.df.apply(lambda row: row[term][::-1], axis=1)

    def __bool__(self):
        return len(self.df[self.df['pt'] != self.df['term']]) == 0

    def flip(self, term):
        matches = self.df['pt'] == term
        self.df.loc[matches, 'term'] = term

        return len(self.df[matches])
