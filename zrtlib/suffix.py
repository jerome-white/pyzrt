import random
from collections import defaultdict

class NGramDict(defaultdict):
    def __getitem__(self, key):
        if key in self:
            sample = random.choice(self.keys())
            if len(sample) != len(key):
                raise KeyError()
            
        return super().__getitem__()

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
            self.tree[head].add(tail, token)

    def get(self, ngram, n=None):
        if n is None:
            for i in self.tree.keys():
                n = len(i)
                break
            
        (head, tail) = self.split(ngram, n)

        if head in self.tokens:
            if not tail:
                yield from self.tokens[head].occurences
            else:
                return self.get(tail)
        else:
            raise KeyError()
