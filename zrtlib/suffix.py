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

class Suffix:
    def __init__(self):
        self.tokens = []
        self.suffixes = NGramDict(Suffix)

    def split(self, ngram, pos=1):
        return (ngram[0:pos], ngram[pos:])
        
    def add(self, ngram, token, root_key_length=1):
        (head, tail) = self.split(ngram, root_key_length)

        if not tail:
            self.tokens.append(token)
        else:
            suffix = self.suffixes[head]
            suffix.add(tail, token)

    def get(self, ngram):
        if not self.suffixes:
            raise KeyError('Tree is empty')

        (head, tail) = self.split(ngram, self.suffixes.key_length)

        if head not in self.suffixes:
            raise KeyError('{0} is not in the tree'.format(head))
        elif not tail:
            suffix = self.suffixes[head]
            yield from suffix.tokens
        else:
            return self.get(tail)

    def ngrams(self, length):
        if not self.suffixes or length < self.suffixes.key_length:
            raise KeyError('Invalid length request')
        elif length == self.suffixes.key_length:
            yield from self.suffixes.keys()
        else:
            length -= self.suffixes.key_length
            for (i, j) in self.suffixes.items():
                yield from map(lambda x: i + x, j.ngrams(length))

    def dump(self, ngram='', level=0):
        print(' ' * level, ngram, ': ', self.tokens, sep='')
        for (i, j) in self.suffixes.items():
            j.dump(ngram + i, level + 1)
