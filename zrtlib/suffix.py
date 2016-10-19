import csv
import operator as op
import itertools
from collections import defaultdict

from zrtlib import zutils

def cut(word, pos=1):
    return (word[0:pos], word[pos:])

class NGramDict(defaultdict):
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
    def __init__(self):
        self.tokens = []
        self.suffixes = NGramDict(type(self))

    def add(self, ngram, token, root_key_length=1):
        (head, tail) = cut(ngram, root_key_length)

        suffix = self.suffixes[head]
        if tail:
            suffix.add(tail, token)
        else:
            suffix.tokens.append(token)

    def get(self, ngram):
        (head, tail) = cut(ngram, self.suffixes.key_length)

        if head in self.suffixes:
            suffix = self.suffixes[head]
            if tail:
                yield from suffix.get(tail)
            elif suffix.tokens:
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

    def write(self, path):
        with path.open('w') as fp:
            writer = csv.writer(fp)
            for (i, j) in self.each():
                writer.writerow([ i ] + [ repr(x) for x in j ])

    def read(self, path, token_factory):
        with path.open() as fp:
            reader = csv.reader(fp)
            min_key = zutils.minval(reader)

            fp.seek(0)
            for (ngram, *tokens) in reader:
                for i in tokens:
                    tok = token_factory(i)
                    self.add(ngram, tok, min_key)

    def prune(self, frequency, relation=op.le):
        if relation(len(self.tokens), frequency):
            self.tokens.clear()

        notok = []
        for (i, j) in self.suffixes.items():
            j.prune(frequency, relation)
            if not j.tokens:
                notok.append(i)
        for i in notok:
            del self.suffixes[i]
