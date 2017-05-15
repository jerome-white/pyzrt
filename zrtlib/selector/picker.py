import io

import pandas as pd

from zrtlib.document import TermDocument

class Picker:
    def add(self, term):
        raise NotImplementedError()

    def __str__(self):
        raise NotImplementedError()

class HiddenQuery(Picker):
    def __init__(self, hidden_document):
        self.document = hidden_document

    def __float__(self):
        return float(self.document)

    def __str__(self):
        return str(self.document)

    def add(self, term):
        if not self.document:
            raise BufferError()

        return self.document.flip(term) > 0

class ProgressiveQuery(Picker):
    def __init__(self):
        self.terms = []

    def __float__(self):
        return float(len(self.terms))

    def __str__(self):
        return ' '.join(self.terms)

    def add(self, term):
        self.terms.append(term)

        return True
