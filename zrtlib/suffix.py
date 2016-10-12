from collections import defaultdict

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
        self.suffixes = NGramDict(SuffixTree)

    def split(self, ngram, pos=1):
        return (ngram[0:pos], ngram[pos:])
        
    def add(self, ngram, token, root_key_length=1):
        (head, tail) = self.split(ngram, root_key_length)

        suffix = self.suffixes[head]
        if not tail:
            suffix.tokens.append(token)
        else:
            suffix.add(tail, token)

    def get(self, ngram):
        (head, tail) = self.split(ngram, self.suffixes.key_length)

        if head in self.suffixes:
            suffix = self.suffixes[head]
            yield from suffix.tokens if not tail else suffix.get(tail)

    def ngrams(self, length):
        if length == self.suffixes.key_length:
            yield from self.suffixes.keys()
        else:
            for (i, j) in self.suffixes.items():
                for k in j.ngrams(length - self.suffixes.key_length):
                    yield i + k

    def dump(self, ngram='', level=0):
        print('-' * level, ngram, ' : ', self.tokens, sep='')
        for (i, j) in self.suffixes.items():
            j.dump(ngram + i, level + 1)
