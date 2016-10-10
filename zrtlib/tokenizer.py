import itertools
import collections

# from zrtlib import logger

class Deque(collections.deque):
    def __init__(self, block_size, skip):
        self.exposed = block_size
        maxlen = self.exposed + skip
        super().__init__(maxlen=maxlen)

    def full(self):
        return len(self) == self.maxlen

    def visible(self):
        yield from itertools.islice(self, 0, self.exposed)

class Character:
    '''
    Portion of a token within a single file
    '''
    def __init__(self, docno, start, end):
        self.docno = docno
        self.start = start
        self.end = end

    def __lt__(self, other):
        return self.start < other.start

    def __len__(self):
        return self.end - self.start

    def tolist(self):
        return [ self.docno, self.start, self.end ]

class Token(list):
    '''
    A collection of characters
    '''
    def __int__(self):
        return sum(map(len, self))

###########################################################################

class Sequencer:
    def __init__(self, corpus, block_size=1, skip=0):
        self.corpus = corpus
        self.block_size = block_size
        self.skip = skip

    def stream(self, offset=0):
        for i in self.corpus:
            length = i.stat().st_size
            yield from map(lambda x: (i.name, x), range(offset, length))
            offset = min(0, offset - length - 1)

    def sequence(self, offset=0):
        key = 0
        segment = Deque(self.block_size, self.skip)

        for i in self.stream(offset):
            segment.append(i)
            if segment.full():
                d = collections.OrderedDict()
                
                for (name, order) in segment.visible():
                    if name not in d:
                        d[name] = []
                    d[name].append(order)
                
                for (name, value) in d.items():
                    (start, stop) = [ x(value) for x in (min, max) ]
                    character = Character(name, start, stop + 1)
                    yield (key, character)

                key += 1
                self.slide(segment)

    def slide(self, segment):
        raise NotImplementedError()

class CharacterSequencer(Sequencer):
    def slide(self, segment):
        segment.clear()

class WindowSequencer(Sequencer):
    def slide(self, segment):
        for _ in range(self.skip + 1):
            segment.popleft()
    
###########################################################################

class Transcriber:
    def __init__(self, token, corpus):
        self.token = token
        self.corpus = corpus
        
    def __str__(self):
        return ''.join(map(self.transcribe, self.token))

    def transcribe(self, char):
        raise NotImplementedError()

# corpus is a dictionary of file offset pointers
class CorpusTranscriber(Transcriber):
    def transcribe(self, char):
        document = self.corpus[char.docno]
        return document[char.start:char.end]
    
# corpus: top level corpus directory
class FileTranscriber(Transcriber):
    def transcribe(self, char):
        path = self.corpus.joinpath(char.docno)
        with path.open() as fp:
            fp.seek(char.start)
            return fp.read(char.end - char.start)

###########################################################################

class Tokenizer:
    def __init__(self, stream):
        self.stream = stream
    
    def each(self):
        token = Token()
        previous = None
        
        for row in self.stream:
            docno = row.pop(1)
            (current, start, end) = map(int, row)
            
            if previous is not None and previous != current:
                yield (previous, sorted(token))
                token = Token()

            character = Character(docno, start, end)
            token.append(character)
            previous = current
            
        # since the last line of the file doesn't get included
        if token:
            yield (previous, sorted(token))
