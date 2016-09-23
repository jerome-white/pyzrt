import csv
from pathlib import Path

class Notebook:
    def __init__(self, key=0):
        self.key = key
        self.length = 0
        self.reported = False
        self.remaining = None

class Gram:
    def __init__(self, docno, start, end):
        self.docno = docno
        self.start = start
        self.end = end

    def __lt__(self, other):
        return self.start < other.start

    def __dir__(self):
        self.items = [ self.docno, self.start, self.end ]

class Token(list):
    '''
    A collection of grams
    '''
    def __int__(self):
        return sum([ x.end - x.start for x in self ])

###########################################################################

class Sequencer:
    def __init__(self, corpus, block_size):
        self.corpus = corpus
        self.block_size = block_size

    def range(self, start, stop, step, offset=None):
        i = start
        while i < stop:
            if offset is None:
                j = i + step
            else:
                j = i + offset
                offset = None
            j = min(j, stop)
            
            yield (i, j)
            i = self.slide(i, j)

    def sequence(self):
        n = Notebook()
        
        for c in self.corpus:
            stop = c.stat().st_size
            for (i, j) in self.range(0, stop, self.block_size, n.remaining):
                yield (n.key, Gram(c.name, i, j))
                n.reported = True
                
                n.length += j - i
                assert(n.length <= self.block_size)
                
                if n.length == self.block_size:
                    n = Notebook(n.key + 1)
                    
            if not n.reported:
                n.remaining = self.block_size - n.length

        if not n.reported:
            yield (n.key, Gram(c.name, i, j))

    def slide(self, i, j):
        raise NotImplementedError()

class CharacterSequencer(Sequencer):
    def slide(self, i, j):
        return j

class WindowedSequencer(Sequencer):
    def slide(self, i, j):
        return i + 1
    
###########################################################################

class Transcriber:
    def __init__(self, token, corpus):
        self.token = token
        self.corpus = corpus
        
    def __str__(self):
        return ''.join(map(self.build, self.token))

    def transcribe(self, gram):
        raise NotImplementedError()

# corpus is a dictionary of file offset pointers
class CorpusTranscriber(Transcriber):
    def transcribe(self, gram):
        document = self.corpus[gram.docno]
        return document[gram.start:gram.end]
    
# corpus: top level corpus directory
class FileTranscriber(Transcriber):
    def transcribe(self, gram):
        path = self.corpus.joinpath(gram.docno)
        with path.open() as fp:
            fp.seek(gram.start)
            return fp.read(gram.end - gram.start)

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

            gram = Gram(docno, start, end)
            token.append(gram)
            previous = current
            
        # since the last line of the file doesn't get included
        if token:
            yield (previous, sorted(token))

    # def write(self, token_fp=sys.stdout, tokenizer):
    #     writer = csv.writer(token_fp)
    #     for row in tokenizer:
    #         writer.writerow(row)
