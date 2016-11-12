class TermWriter:
    def __init__(self, path, prefix='pt', delimiter=','):
        self.path = path
        self.delimiter = delimiter
        self.prefix = prefix

    def write(self, term, ngram, token):
        p = path.joinpath(token.docno.stem)
        with p.open('a') as fp:
            print(term, ngram, token.start, token.end,
                  sep=self.delimiter, file=fp)
