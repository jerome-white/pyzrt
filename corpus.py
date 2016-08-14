from pathlib import Path

class Notes:
    def __init__(self, key=0):
        self.key = key
        self.length = 0
        self.fragment = 0
        self.remaining = None
        
def orange(self, start, stop, step, offset=None):
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

def fragment(self, corpus_listing, block_size=1):
    n = Notebook()
    
    for (docno, doc) in corpus_files:
        for (i, j) in orange(0, len(doc.data), block_size, n.remaining):
            yield (n.key, n.fragment, docno, i, j)
            n.length += j - i
            assert(n.length <= block_size)
                
            if n.length == block_size:
                n = Notebook(n.key + 1)
            else:
                n.fragment += 1

        if n.fragment:
            n.remaining = block_size - n.length

    if n.fragment:
        yield (n.key, n.fragment, docno, i, j)

def to_string(fragment, corpus):
    string = []
        
    for (docno, start, end) in fragment:
        document = corpus[docno]
        s = document.data[start:end]
        string.append(s)
            
    return ''.join(string)
