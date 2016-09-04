from pathlib import Path
from itertools import islice

class Notebook:
    def __init__(self, key=0):
        self.key = key
        self.length = 0
        self.fragment = 0
        self.reported = False
        self.remaining = None
        
def orange(start, stop, step, offset=None):
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

def fragment(corpus_listing, block_size=1):
    n = Notebook()
    
    for path in corpus_listing:
        for (i, j) in orange(0, path.stat().st_size, block_size, n.remaining):
            yield (n.key, n.fragment, path.name, i, j)
            n.reported = True
            
            n.length += j - i
            assert(n.length <= block_size)
                
            if n.length == block_size:
                n = Notebook(n.key + 1)
            else:
                n.fragment += 1

        if n.fragment:
            n.remaining = block_size - n.length

    if n.fragment and not n.reported:
        yield (n.key, n.fragment, path.name, i, j)

def to_string(chunk, corpus=None, corpus_directory=None):
    assert(corpus or corpus_directory)
    
    string = []
    
    for (docno, start, end) in chunk:
        if corpus:
            data = corpus[docno][start:end]
        else:
            path = Path(corpus_directory, docno)
            with path.open() as fp:
                fp.seek(start)
                data = fp.read(end - start)

        string.append(data)

    return ''.join(string)
