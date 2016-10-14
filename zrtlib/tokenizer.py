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

###########################################################################

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

###########################################################################

class Sequencer:
    def __init__(self, corpus, block_size=1, skip=0, offset=0):
        self.corpus = corpus
        self.block_size = block_size
        self.skip = skip
        self.offset = offset

    def __iter__(self):
        key = 0
        segment = Deque(self.block_size, self.skip)

        for i in self.stream():
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

    def stream(self):
        offset = self.offset

        for i in self.corpus:
            length = i.stat().st_size
            yield from map(lambda x: (i, x), range(offset, length))
            offset = min(0, offset - length - 1)

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

class Tokenizer:
    def __init__(self, stream):
        self.stream = stream
    
    def __iter__(self):
        token = Token()
        previous = None
        
        for (current, character) in self.stream:
            if previous is not None and previous != current:
                yield (previous, sorted(token))
                token = Token()

            token.append(character)
            previous = current
            
        # since the last line of the file doesn't get included
        if token:
            yield (previous, sorted(token))
