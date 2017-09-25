import operator as op
from collections import namedtuple

import pandas as pd

class Region:
    def __init__(self, n, first, last, df):
        self.n = n
        self.first = first
        self.last = last
        self.df = df

    def sequential(self):
        previous = None

        for row in self.df.itertuples():
            current = (row.start, row.end)
            if previous is not None:
                print(current, previous)
                if any([ op.sub(*x) != 1 for x in zip(current, previous) ]):
                    return False
            previous = current

        return True

    def homogenous(self):
        return self.df['length'].unique().size == 1

class TermDocument:
    def __init__(self, document, include_lengths=True):
        self.name = getattr(document, 'stem', None)
        self.df = pd.read_csv(document)
        self.df.sort_values(by=[ 'start', 'end' ], inplace=True)

        regions = []
        for row in self.df.itertuples():
            if regions:
                (region, end) = regions[-1]
                region += int(row.start > end)
            else:
                region = 0
            regions.append((region, row.end))

        kwargs = { 'region': list(map(op.itemgetter(0), regions)) }
        if include_lengths:
            kwargs['length'] = lambda x: x.end - x.start
        self.df = self.df.assign(**kwargs)

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
