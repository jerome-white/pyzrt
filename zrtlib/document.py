from collections import namedtuple

import pandas as pd

Region = namedtuple('Region', 'n, first, last, df')

class TermDocument:
    def __init__(self, document, include_lengths=True):
        self.name = document.stem

        self.df = pd.read_csv(str(document))
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
    columns = {
        'hidden': 'term',
        'visible': 'original',
    }

    def __init__(self, document, include_lengths=True):
        super().__init__(document, include_lengths)

        # rename visible term column
        columns = { self.columns['hidden']: self.columns['visible'] }
        self.df.rename(columns=columns, inplace=True)

        # flip original terms
        flip = lambda row: row[self.columns['visible']][::-1]
        self.df[self.columns['hidden']] = self.df.apply(flip, axis=1)

    def __bool__(self):
        '''
        True if hidden terms remain
        '''
        (x, y) = self.columns.values()
        remaining = self.df[self.df[x] != self.df[y]]

        return not remaining.empty

    def flip(self, term):
        matches = self.df[self.columns['visible']] == term
        self.df.loc[matches, self.columns['hidden']] = term

        return self.df[matches]

    def reveal(self):
        for i in self.df[self.columns['hidden']].unique():
            self.flip(i)
