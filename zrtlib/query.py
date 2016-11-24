import pandas as pd

class TermDoc:
    def __init__(self, doc):
        self.df = pd.read_csv(doc)
        self.df.sort_values(by=[ 'start', 'end' ], inplace=True)

    def __str__(self):
        return self.df.to_csv(columns=[ 'term' ],
                              header=False,
                              index=False,
                              line_terminator=' ',
                              sep=' ')
