import operator as op
from pathlib import Path
from collections import namedtuple, defaultdict

IndexedToken = namedtuple('IndexedToken', 'index, tokens')

class Posting(defaultdict):
    def __init__(self, token_stream, to_string):
        super().__init__(list)

        for (i, tokens) in enumerate(token_stream):
            tok = to_string(tokens)
            self[tok].append(IndexedToken(i, tokens))
    
    def frequency(self, token):
        return len(self[token])

    def mass(self, token, relative=True):
        counter = { x: sum([ len(z) for z in y ]) for (x, y) in self.items() }
        c = counter[token]

        return c / sum(counter.values()) if relative else c

    def weight(self, token):
        freq = self.frequency(token)
        keys = set(self.keys())
        
        n = max(map(self.frequency, keys.difference([ token ])))

        return freq / n

    def each(self, index):
        yield from map(op.attrgetter('index'), self[index])

    def tokens(self):
        sum([ len(x) * len(y) for (x, y) in self.items() ])
