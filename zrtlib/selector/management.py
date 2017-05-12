from collections import deque

import pandas as pd

class TermSelector:
    def __init__(self, strategy, feedback, seed=None):
        self.strategy = strategy
        self.feedback = feedback
        self.seed = deque(seed) if seed is not None else []

        self.df = None
        self.documents = {}

    #
    # Set up the DataFrame used by the selectors
    #
    def __iter__(self):
        self.df = pd.concat(self.documents.values(), copy=False)
        self.df.reset_index(drop=True, inplace=True)

        return self

    #
    # Each iteration presents the dataframe to the strategy and marks
    # the choice as selected
    #
    def __next__(self):
        if self.seed:
            term = self.seed.popleft()
        else:
            term = self.strategy.pick(self.df, self.feedback)
        self.mark_selected(term)

        return term

    #
    # mark the term as being selected
    #
    def mark_selected(self, term, order=None):
        matches = self.df['term'] == term
        if matches.empty:
            return

        if order is None:
            order = self.df['selected'].max() + 1
        self.df.loc[matches, 'selected'] = order

    #
    # Add documents to the corpus
    #
    def add(self, document):
        assert(document.name not in self.documents)

        new_columns = {
            'document': document.name,
            'selected': 0,
        }
        self.documents[document.name] = document.df.assign(**new_columns)
