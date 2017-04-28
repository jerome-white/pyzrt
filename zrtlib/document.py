from collections import namedtuple

import pandas as pd

Region = namedtuple('Region', 'n, first, last, df')

class TermDocument:
    def __init__(self, document, include_lengths=True):
        self.name = document.stem

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

    #
    # True if hidden terms remain
    #
    def __bool__(self):
        return float(self) > 0

    #
    # Percentage of terms that are hidden
    #
    def __float__(self):
        return len(self.hidden()) / len(self.df)

    def hidden(self):
        (x, y) = self.columns.values()
        return self.df[self.df[x] != self.df[y]]

    def flip(self, term=None, which='visible'):
        focus = self.columns[which]

        if term is None:
            potentials = self.hidden()
            if potentials.empty:
                return 0
            term = potentials[focus].sample().get_value(0, takeable=True)

        matches = self.df[focus] == term
        flipped = matches[matches == True].sum()
        if flipped > 0:
            other = 'hidden' if which == 'visible' else 'visible'
            self.df.loc[matches, self.columns[other]] = term

        return flipped

    def reveal(self):
        col = 'visible'
        for i in self.df[self.columns[col]].unique():
            self.flip(i, col)
