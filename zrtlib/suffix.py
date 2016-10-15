from collections import defaultdict

def cut(word, pos=1):
    return (word[0:pos], word[pos:])

class NGramDict(defaultdict):
    def __init__(self, default_factory, *args):
        super().__init__(default_factory, *args)
        self.key_length = None
        
    def __getitem__(self, key):
        key_length = len(key)
        
        if self.key_length is None:
            self.key_length = key_length
        elif self.key_length != key_length:
            msg = 'Invalid key length: attempted {0} ("{1}"), required {2}'
            raise KeyError(msg.format(key_length, key, self.key_length))
        
        return super().__getitem__(key)

class SuffixTree:
    def __init__(self):
        self.tokens = []
        self.suffixes = NGramDict(type(self))

    def add(self, ngram, token, root_key_length=1):
        (head, tail) = cut(ngram, root_key_length)

        suffix = self.suffixes[head]
        if not tail:
            suffix.tokens.append(token)
        else:
            suffix.add(tail, token)

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
            if length == self.suffixes.key_length:
                if j.tokens:
                    yield i
            else:
                for k in j.ngrams(length - self.suffixes.key_length):
                    yield i + k

    def each(self, ngram=''):
        if self.tokens:
            yield (ngram, self.tokens)

        for (i, j) in self.suffixes.items():
            yield from j.each(ngram + i)

class DebugSuffixTree(SuffixTree):
    def dump(self, ngram='', level=0):
        print('-' * level, ngram, ' : ', self.tokens, sep='')
        for (i, j) in self.suffixes.items():
            j.dump(ngram + i, level + 1)
