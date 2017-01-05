class TermSelector:
    def __init__(self):
        self.documents = []

    def __iter__(self):
        raise NotImplementedError

    def add(self, document):
        self.documents.append(document)

class RandomSelector(TermSelector):
    def __init__(self):
        super().__init__()
        
        self.terms = set()
        
    def __iter__(self):
        yield from self.terms

    def add(self, document):
        self.terms.update(document.term.values)
