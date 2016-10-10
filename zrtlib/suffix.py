from collections import defaultdict

class NGramDict(defaultdict):
    def __init__(self, default_factory, *args):
        super().__init__(default_factory, *args)
        self.n = None
        
    def __getitem__(self, key):
        n = len(key)
        
        if self.n is None:
            self.n = n
        elif self.n != n:
            msg = 'Invalid key length: attempted {0} ("{1}"), required {2}'
            raise KeyError(msg.format(n, key, self.n))
        
        return super().__getitem__(key)

class Suffix:
    def __init__(self):
        self.tokens = []
        self.tree = NGramDict(Suffix)

    def split(self, ngram, pos=1):
        return (ngram[0:pos], ngram[pos:])
        
    def add(self, ngram, token, root_key_length=1):
        (head, tail) = self.split(ngram, root_key_length)

        if not tail:
            self.tokens.append(token)
        else:
            suffix = self.tree[head]
            suffix.add(tail, token)

    def get(self, ngram):
        (head, tail) = self.split(ngram, self.tree.n)

        if head not in self.tokens:
            raise KeyError()
        elif not tail:
            suffix = self.tokens[head]
            yield from suffix.occurences
        else:
            return self.get(tail)
