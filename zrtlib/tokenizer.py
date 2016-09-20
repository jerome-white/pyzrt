import sys
import csv
from pathlib import Path

class Notebook:
    def __init__(self, key=0):
        self.key = key
        self.length = 0
        self.reported = False
        self.remaining = None
        
class Token:
    def __init__(self, docno, start, end):
        self.docno = docno
        self.start = start
        self.end = end

    def __lt__(self, other):
        return self.start < other.start

    def __dir__(self):
        self.items = [ self.docno, self.start, self.end ]

class Segment(list):
    def __sizeof__(self):
        return sum([ x.end - x.start for x in self ])

####

class Tokenizer:
    def __init__(self, corpus):
        self.corpus = corpus

    def tokenize(self):
        raise StopIteration()

class CharacterTokenizer(Tokenizer):
    def __init__(self, corpus, characters=1):
        super().__init__(corpus)
        self.characters = characters
        
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
            i = j

    def tokenize(self):
        n = Notebook()
        
        for c in self.corpus:
            stop = c.stat().st_size
            for (i, j) in self.range(0, stop, self.characters, n.remaining):
                yield (n.key, Token(c.name, i, j))
                n.reported = True
                
                n.length += j - i
                assert(n.length <= self.characters)
                
                if n.length == self.characters:
                    n = Notebook(n.key + 1)
                    
            if not n.reported:
                n.remaining = self.characters - n.length

        if not n.reported:
            yield (n.key, Token(c.name, i, j))

###

class TokenBuilder:
    def __init__(self, segment, corpus):
        self.segment = segment
        self.corpus = corpus
        
    def __str__(self):
        return ''.join(map(self.build, self.segment))

    def build(self, token):
        raise NotImplementedError()

# corpus is a dictionary of file offset pointers
class CorpusTokenBuilder(TokenBuilder):
    def build(self, token):
        document = self.corpus[token.docno]
        return document[token.start:token.end]
    
# corpus: top level corpus directory
class FileTokenBuilder(TokenBuilder):
    def build(self, token):
        path = self.corpus.joinpath(token.docno)
        with path.open() as fp:
            fp.seek(token.start)
            return fp.read(token.end - token.start)

###

class Segmenter:
    def __init__(self, stream):
        self.stream = stream
    
    def each(self):
        segment = Segment()
        previous = None
        
        for row in self.stream:
            docno = row.pop(1)
            (current, start, end) = map(int, row)
        
            if previous is not None and previous != current:
                yield (previous, sorted(segment))
                segment = Segment()
            
            segment.append(Token(docno, start, end))
            previous = current
            
        # since the last line of the file doesn't get included
        if segment:
            yield (previous, sorted(segment))

    # def write(self, token_fp=sys.stdout, tokenizer):
    #     writer = csv.writer(token_fp)
    #     for row in tokenizer:
    #         writer.writerow(row)
