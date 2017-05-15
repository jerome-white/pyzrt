import io

import pandas as pd

from zrtlib.document import TermDocument

class Picker:
    def add(self, term):
        raise NotImplementedError()

    def terms(self):
        raise NotImplementedError()

class HiddenQuery(Picker):
    def __init__(self, hidden_document):
        self.document = hidden_document

    def __float__(self):
        return float(self.document)

    def add(self, term):
        if not self.document:
            raise BufferError()

        return self.document.flip(term) > 0

    def terms(self):
        return self.document

class ProgressiveQuery(Picker):
    def __init__(self):
        self.df = pd.DataFrame()

    def __float__(self):
        return float(len(self.df))

    def add(self, term):
        self.df = self.df.append(term, ignore_index=True)

        return True

    def terms(self):
        return TermDocument(io.StringIO(self.df.to_csv(index=False)))
