import csv
import operator as op
import collections

from zrtlib import zutils

def suffix_builder(path, token_parser, token_factory=None):
    s = SuffixTree(token_factory)
    with path.open() as fp:
        s.read(fp, token_parser)

    return s

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
    def __init__(self, token_factory=None):
        if token_factory is None:
            token_factory = set

        self.tokens = token_factory()
        self.suffixes = NGramDict(self.factory(token_factory))

    def __len__(self):
        return len(list(self.each()))

    def factory(self, token_factory):
        return lambda: type(self)(token_factory)

    def add(self, ngram, token, root_key_length=1):
        (head, tail) = zutils.cut(ngram, root_key_length)

        suffix = self.suffixes[head]
        if tail:
            suffix.add(tail, token)
        else:
            suffix.tokens.add(token)

    def lookup(self, ngram):
        (head, tail) = zutils.cut(ngram, self.suffixes.key_length)

        if head in self.suffixes:
            suffix = self.suffixes[head]
            return suffix.lookup(tail) if tail else suffix

    def get(self, ngram):
        suffix = self.lookup(ngram)
        if suffix:
            yield from suffix.tokens

    def ngrams(self, length):
        for (i, j) in self.suffixes.items():
            correct_level = length == self.suffixes.key_length
            if correct_level and j.tokens:
                yield i
            elif not correct_level:
                for k in j.ngrams(length - self.suffixes.key_length):
                    yield i + k

    def each(self, ngram=''):
        if self.tokens:
            yield (ngram, self.tokens)

        for (i, j) in self.suffixes.items():
            yield from j.each(ngram + i)

    def write(self, fp):
        writer = csv.writer(fp)
        for (i, j) in self.each():
            writer.writerow([ i ] + [ repr(x) for x in j ])

    def read(self, fp, token_parser):
        reader = csv.reader(fp)
        min_key = zutils.minval(reader)

        fp.seek(0)
        for (ngram, *tokens) in reader:
            for i in map(token_parser, tokens):
                self.add(ngram, i, min_key)

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
    # Remove n-grams whose locations are subsets of immediate larger
    # n-grams.
    #
    def compress(self):
        for i in self.suffixes.values():
            if self.tokens and self.tokens.issubset(i.tokens):
                self.tokens.clear()
            i.compress()

    #
    # Remove n-grams whose locations are subsets of larger n-grams in
    # the chain (n-grams with the same prefix).
    #
    def exists(self, tokens):
        for i in self.suffixes.values():
            if tokens.issubset(i.tokens) or i.exists(tokens):
                return True

        return False

    def collapse(self):
        if self.tokens and self.exists(self.tokens):
            self.tokens.clear()

        for j in self.suffixes.values():
            j.collapse()

    #
    # Remove n-grams whose location is subsumed by any other n-gram
    # in the tree (no-prefix condition).
    #
    def fold(self):
        c = collections.Counter([ len(x) for (x, _) in self.each() ])
        if len(c) < 2:
            return
        (x, y) = [ x(c.keys()) for x in (min, max) ]

        for i in zutils.count(x + 1, y):
            for j in self.ngrams(i):
                sr = self.lookup(j)
                for k in zutils.substrings(j):
                    jr = self.lookup(k)
                    if jr and jr.tokens.issubset(sr.tokens):
                        jr.tokens.clear()

        self.prune()
