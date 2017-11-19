class Regionalize:
    def __init__(self, document):
        self.document = document

    def __iter__(self):
        raise NotImplementedError()

class PerRegion(Regionalize):
    def __iter__(self):
        yield from self.document.regions()

class CollectionAtOnce(Regionalize):
    def __iter__(self):
        yield self.document
