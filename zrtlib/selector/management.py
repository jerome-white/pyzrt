import pandas as pd

class TermSelector:
    def __init__(self, strategy):
        self.strategy = strategy
        self.df = None
        self.feedback = None
        self.documents = {}

    #
    # Set up the DataFrame used by the selectors
    #
    def __iter__(self):
        self.df = pd.concat(self.documents.values(), copy=False)

        return self

    #
    # Each iteration presents the dataframe to the strategy manager
    #
    def __next__(self):
        # pass on to strategy
        try:
            term = self.strategy.pick(self.df, self.feedback)
        except LookupError:
            raise StopIteration()
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
