import operator as op
from pathlib import Path
from collections import defaultdict

from zrtlib.corpus import Character

class Token(tuple):
    '''
    A collection of Characters
    '''
    def __int__(self):
        return sum(map(len, self))

    def __repr__(self):
        return ' '.join(map(str, self))
    
    def __str__(self):
        def transcribe(char):
            with char.docno.open() as fp:
                fp.seek(char.start)
                return fp.read(len(char))

        return self.collect(transcribe)

    def tostring(self, corpus):
        def transcribe(char):
            document = corpus[char.docno]
            return document[char.start:char.end]

        return self.collect(transcribe)

    def collect(self, transcribe):
        return ''.join(map(transcribe, self))

    def between(self, other):
        compare = lambda x, y, z: z(x, y) or not (z(x, y) or z(y, x))

        for (i, j) in zip((0, -1), (op.lt, op.gt)):
            (x, y) = map(op.itemgetter(i), (self, other))
            if not compare(y, x, j):
                return False

        return True

class TokenSet(set):
    def issubset(self, other):
        d = defaultdict(bool)

        for i in self:
            for j in other:
                d[i] |= i.between(j)
                if d[i]:
                    break

        return all(d.values())

class Tokenizer:
    def __init__(self, stream):
        self.stream = stream
    
    def __iter__(self):
        token = []
        previous = None
        
        for (current, character) in self.stream:
            if previous is not None and previous != current:
                yield (previous, Token(token))
                token = []

            token.append(character)
            previous = current
            
        # since the last line of the file doesn't get included
        if token:
            yield (previous, Token(token))

def unstream(string, sep=' ', ch_attrs=3):
    line = []
    token = []

    for i in string.split(sep):
        line.append(i)
        if len(line) == ch_attrs:
            docno = Path(line[0])
            (start, stop) = map(int, line[1:])
            token.append(Character(docno, start, stop))
            line = []

    return Token(token)
