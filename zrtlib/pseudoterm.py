import csv

class PseudoTermWriter:
    def __init__(self, suffix, prefix='pt'):
        self.suffix = suffix
        self.ngrams = len(str(len(self.suffix)))
        self.prefix = prefix

    #
    # Create (pseudo)terms
    #
    def write(self, path):
        for (i, (ngram, collection)) in enumerate(self.suffix.each()):
            pt = self.prefix + str(i).zfill(self.ngrams)
            for token in collection:
                for t in token:
                    p = path.joinpath(t.docno.stem)
                    with p.open('a') as fp:
                        writer = csv.writer(fp)
                        writer.writerow([ pt, ngram, t.start, t.end ])
