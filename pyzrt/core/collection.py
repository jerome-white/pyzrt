import csv
import operator as op
import itertools as it

from pyzrt.core.term import Term

class TermCollection(list):
    '''
    A collection of Terms

    Attributes
    ----------
    collection : Path | NoneType
        Path to the term file this instance represents
    '''

    def __init__(self, collection=None, reader=None):
        '''
        Parameters
        ----------
        collection : Path, optional
           Path object representing location of the the term file
           to be parsed. If None, then the instantiated
           collection will be empty

        reader : iterable, optional
           Given a file object (generally the path represented by
           collection) generate tuples that are capable of being
           made into Term's. If None, dictionaries are created
           from each line, which in turn are used to make Term's.

        See Also
        ----------
        Term : namedtuple
        '''

        self.collection = collection

        if self.collection:
            with self.collection.open() as fp:
                if reader is None:
                    f = Term._fromdict
                    reader = TermCollection.reader
                else:
                    f = lambda x: Term(*x)
                self.extend(map(f, reader(fp)))
            self.sort()

    def __repr__(self):
        return self.collection.stem if self.collection else ''

    def __str__(self):
        return self.tostring(repr)

    def tostring(self, how, separator=' '):
        '''Create a string from terms in the collection

        Parameters
        ----------
        how : Term -> str
           Function mapping a Term objec to a string

        separator : str, optional
           String used to separate individual Term's
        '''

        return separator.join(map(how, self))

    def tocsv(self, fp, header=True):
        '''Write a collection to CSV format.

        Parameters
        ----------
        fp : file-object
           An open file stream

        header : bool, optional
           Whether to write the Term information as a header.
        '''

        writer = csv.DictWriter(fp, fieldnames=Term._fields)
        if header:
            writer.writeheader()
        writer.writerows(map(op.methodcaller('_asdict'), self))

    def bylength(self, descending=True):
        '''Sort the collections by Term length

        Parameters
        ----------
        descending : Boolean, optional
           Whether result should be in descending order
        '''

        self.sort(key=len, reverse=descending)

    def get(self, ngram):
        '''Get a Term and its respective index based on an ngram

        Parameters
        ----------
        ngram : str
           n-gram to find within the collection

        Yields
        ----------
        (int, Term)
           The Term matching this ngram, along with the Term's
           index in the collection
        '''

        for (i, term) in enumerate(self):
            if term.ngram == ngram:
                yield (i, term)

    def regions(self, start=0, follows=None):
        '''Generate each overlapping region as a new collection.

        Parameters
        ----------
        start : int, optional
           n-gram to find within the collection

        follows : Term,Term -> bool , optional
           Given two terms, returns True iff the
           terms "overlap". Terms are presented to the function
           in sequential order (previous, current).

        Yields
        ----------
        TermCollection
           An overlapping region relative to, and subset of, the
           calling collection.

        Raises
        ----------
        AssertionError
           If the collection is not in sequential (Term
           less-than) order
        '''

        if follows is None:
            follows = lambda x, y: x.position > y.span

        region = type(self)()

        for current in it.islice(self, start, None):
            if region:
                previous = region[-1]
                assert(previous.position <= current.position) # not in order!
                if follows(current, previous):
                    yield region
                    region = type(self)()
            region.append(current)

        if region:
            yield region

    def after(self, index):
        '''Terms that overlap a Term at a given index.

        Parameters
        ----------
        index : int
           Index within the collection from where to begin.

        Yields
        ----------
        TermCollection
           A single collection. Can also be thought of as the
           first 'region' relative to an index.
        '''

        anchor = self[index]
        follows = lambda x, y: x.position > anchor.span
        distance = 0

        for i in it.islice(self, index, None):
            if i.position > anchor.position:
                break
            distance += 1

        yield from next(self.regions(index + distance, follows))

    @classmethod
    def fromaren(cls, collection):
        '''Convert output from the actual (Aren-authored) term
           detector to a term collection.

        Parameters
        ----------
        collection : Path
           Output from ZRT system

        Returns
        ----------
        TermCollection
        '''
        
        def reader(fp):
            reader = csv.reader(fp, delimiter=' ')
            for (psuedoterm, *position) in reader:
                name = 'pt' + psuedoterm

                (start, end) = map(int, position)
                ngram = 'x' * (end - start + 1)

                yield (name, ngram, start)

        return cls(collection, reader)

    @staticmethod
    def reader(fp, delimiter=',', header=None):
        '''Parse simulator output.

        Parameters
        ----------
        fp: iterable->string
            Any object that supports the iterator protocol and returns
            a string each time its __next__() method is called

        delimiter : str , optional
           String that delimits fields on each line

        header: list , optional
           List of keys to use as the header. If None, uses first line
           of fp

        Yields
        ----------
        dict
           Header is used as keys, fields used as values.

        '''

        for i in fp:
            line = i.strip()

            (x, y) = [ f(delimiter) for f in (line.index, line.rindex) ]
            parts = [
                line[:x],
                line[x+1:y],
                line[y+1:],
            ]

            if header is None:
                header = parts
            else:
                yield dict(zip(header, parts))
