from pyzrt.search.doc import IndriQuery
from pyzrt.retrieval.query import Query

class Picker:
    def __float__(self):
        return float(self.document)

    #
    # Allows a Picker to be passed directly to QueryExecutor::query
    #
    def __str__(self):
        raise NotImplementedError()

    def add(self, term):
        raise NotImplementedError()

class HiddenQuery(Picker):
    def __init__(self, hidden_document, model='ua'):
        self.document = hidden_document
        self.model = model

    def __float__(self):
        return float(self.document)

    def __str__(self):
        return str(Query(self.document, self.model))

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
        indri = IndriQuery()
        indri.add(' '.join(self.terms))

        return str(indri)

    def add(self, term):
        self.terms.append(term)

        return True
