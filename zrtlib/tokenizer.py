import csv
from pathlib import Path

import numpy as np

from zrtlib import logger

class Notebook:
    def __init__(self, key=0):
        self.key = key
        self.length = 0
        self.remaining = None

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

    def tolist(self):
        return [ self.docno, self.start, self.end ]

class Token(list):
    '''
    A collection of characters
    '''
    def __int__(self):
        return sum([ x.end - x.start for x in self ])

###########################################################################

class Sequencer:
    def __init__(self, corpus, block_size=1, skip=0):
        self.corpus = corpus
        self.block_size = block_size
        self.skip = skip

    def window(self, start=0, stop=np.inf, step=1, offset=None):
        i = start
        while i < stop:
            j = i
            if offset is not None:
                j += offset
                offset = None
            else:
                j += step
            j = min(j, stop)
            
            yield (i, j)
            
            if j >= stop:
                break
            i = self.slide(i, j) + self.skip

    def sequence(self):
        log = logger.getlogger()
        n = Notebook()

        for c in self.corpus:
            stop = c.stat().st_size
            log.debug('{0} {1}'.format(c, stop))
            for (i, j) in self.window(0, stop, self.block_size, n.remaining):
                yield (n.key, Character(c.name, i, j))
                
                n.length += j - i
                log.debug('{0} {1} {2}'.format(i, j, n.length, n.remaining))
                assert(n.length <= self.block_size)
                
                if n.length == self.block_size:
                    n = Notebook(n.key + 1)
            n.remaining = self.block_size - n.length

        if n.length > 0:
            yield (n.key, Character(c.name, i, j))

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

            c = Character(docno, start, end)
            token.append(c)
            previous = current
            
        # since the last line of the file doesn't get included
        if token:
            yield (previous, sorted(token))

    # def write(self, token_fp=sys.stdout, tokenizer):
    #     writer = csv.writer(token_fp)
    #     for row in tokenizer:
    #         writer.writerow(row)
