import itertools
import collections

class Deque(collections.deque):
    def __init__(self, block_size, skip):
        self.exposed = block_size
        super().__init__(maxlen=(self.exposed + skip))

    def full(self):
        return len(self) == self.maxlen

    def visible(self):
        yield from itertools.islice(self, 0, self.exposed)

class Character:
    '''
    A segment of one or more characters within a single file
    '''
    def __init__(self, docno, start, end):
        self.docno = docno
        self.start = start
        self.end = end

    def __lt__(self, other):
        return self.docno < other.docno or self.start < other.start

    def __len__(self):
        return self.end - self.start

    def tolist(self):
        return [ self.docno, self.start, self.end ]

class Corpus(list):
    def __init__(self, corpus):
        super().__init__(sorted(corpus.iterdir()))

class CompleteCorpus(collections.OrderedDict):
    def __init__(self, corpus):
        super().__init__()

        for i in Corpus(corpus):
            with i.open() as fp:
                self[i] = fp.read()

    def characters(self):
        return sum(map(len, self.corpus.values()))

class CorpusStreamer:
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
            yield from zip(itertools.repeat(i), range(offset, length))
            offset = max(0, offset - length - 1)

    def slide(self, segment):
        raise NotImplementedError()

class CharacterStreamer(CorpusStreamer):
    def slide(self, segment):
        segment.clear()

class WindowStreamer(CorpusStreamer):
    def slide(self, segment):
        for _ in range(self.skip + 1):
            segment.popleft()
