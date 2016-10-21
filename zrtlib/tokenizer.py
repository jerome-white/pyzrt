from pathlib import Path

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
