import csv
import operator as op
import collections

from zrtlib import zutils

class NGramDict(collections.defaultdict):
    def __init__(self, default_factory, *args):
        super().__init__(default_factory, *args)
        self.key_length = None
        
    def __missing__(self, key):
        self.integrity_check(key)
        return super().__missing__(key)

    def __setitem__(self, key, val):
        self.integrity_check(key)
        super().__setitem__(key, val)

    def integrity_check(self, key):
        k = len(key)
        if self.key_length is None:
            self.key_length = k
        elif self.key_length != k:
            msg = 'Invalid key length: attempted {0} ("{1}"), required {2}'
            raise KeyError(msg.format(k, key, self.key_length))

class SuffixTree:
    #
    # A SuffixTree contains n-grams who point to tokens and other
    # n-grams.
    #
    def __init__(self, token_factory=set):
        self.tokens = token_factory()
        self.suffixes = NGramDict(self.factory(token_factory))

    #
    # The length of a suffix tree is the number of n-grams it
    # contains.
    #
    def __len__(self):
        return len(list(self.each()))

    @classmethod
    def builder(cls, path, token_parser, token_factory=set):
        suffix = cls(token_factory)
        with path.open() as fp:
            suffix.read(fp, token_parser)

        return suffix

    #
    # Method for building new SuffixTree's based on the current
    # instance.
    #
    def factory(self, token_factory):
        return lambda: type(self)(token_factory)

    #
    # Length frequency (number of times each key length appears in the
    # tree)
    #
    def lf(self):
        return collections.Counter([ len(x) for (x, _) in self.each() ])

    #
    # Add an n-gram and corresponding token to the tree.
    #
    def add(self, ngram, token, root_key_length=1):
        (head, tail) = zutils.cut(ngram, root_key_length)

        suffix = self.suffixes[head]
        if tail:
            suffix.add(tail, token)
        else:
            suffix.tokens.add(token)

    #
    # Find the root suffix branch associated with this n-gram
    #
    def lookup(self, ngram):
        (head, tail) = zutils.cut(ngram, self.suffixes.key_length)

        if head in self.suffixes:
            suffix = self.suffixes[head]
            return suffix.lookup(tail) if tail else suffix

    #
    # Get the tokens associated with this n-gram.
    #
    def get(self, ngram):
        suffix = self.lookup(ngram)
        if suffix:
            yield from suffix.tokens

    #
    # Get all n-grams of a certain length.
    #
    def ngrams(self, length):
        for (i, j) in self.suffixes.items():
            correct_level = length == self.suffixes.key_length
            if correct_level and j.tokens:
                yield i
            elif not correct_level:
                for k in j.ngrams(length - self.suffixes.key_length):
                    yield i + k

    #
    # Retrieve all n-grams in the tree.
    #
    def each(self, ngram=''):
        if self.tokens:
            yield (ngram, self.tokens)

        for (i, j) in self.suffixes.items():
            yield from j.each(ngram + i)

    #
    # Write the suffix tree as a CSV file.
    #
    def write(self, fp):
        def f(row):
            for (i, j) in enumerate(row):
                if i == 0:
                    yield j
                else:
                    yield from map(repr, j)

        writer = csv.writer(fp)
        writer.writerows(map(f, self.each()))

    #
    # Insert n-grams from a suffix tree written by 'write'
    #
    def read(self, fp, token_parser):
        reader = csv.reader(fp)
        min_key = zutils.minval(reader)

        fp.seek(0)
        for (ngram, *tokens) in reader:
            for i in map(token_parser, tokens):
                self.add(ngram, i, min_key)

    #
    # Remove suffixes with too few corresponding tokens.
    #
    def prune(self, frequency=0, relation=op.le):
        if relation(len(self.tokens), frequency):
            self.tokens.clear()

        notok = []
        remaining = len(self.tokens)
        for (i, j) in self.suffixes.items():
            pruned = j.prune(frequency, relation)
            if pruned > 0:
                remaining += pruned
            elif not j.tokens:
                notok.append(i)
        for i in notok:
            del self.suffixes[i]

        return remaining

    #
    # Remove n-grams whose location is subsumed by any other n-gram
    # in the tree (no-prefix condition).
    #
    def fold(self, min_gram, max_gram):
        for i in zutils.count(min_gram, max_gram):
            for j in self.ngrams(i):
                sr = None
                for k in zutils.substrings(j):
                    jr = self.lookup(k)
                    if jr:
                        if sr is None:
                            sr = self.lookup(j)
                        if jr.tokens.issubset(sr.tokens):
                            jr.tokens.clear()

    #
    # Convenience method for fold.
    #
    def compress(self, length=None):
        c = self.lf()
        if len(c) > 1:
            if length is None:
                (x, y) = zutils.minmax(c.keys())
                self.fold(x + 1, y)
            else:
                self.fold(length, length)
            self.prune()
