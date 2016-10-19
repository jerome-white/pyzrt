from pathlib import Path

from zrtlib.corpus import Character

class Token(list):
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
        token = Token()
        previous = None
        
        for (current, character) in self.stream:
            if previous is not None and previous != current:
                yield (previous, token)
                token = Token()

            token.append(character)
            previous = current
            
        # since the last line of the file doesn't get included
        if token:
            yield (previous, token)

def unstream(string, ch_attrs=3):
    line = []
    token = Token()

    for i in string.split():
        line.append(i)
        if len(line) == ch_attrs:
            docno = Path(line[0])
            character = Character(docno, *map(int, line[1:]))
            token.append(character)
            line = []

    return token
