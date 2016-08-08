import numpy as np

from collections import namedtuple, OrderedDict

Document = namedtuple('Document', 'fpath, data')
Fragment = namedtuple('Fragment', 'docno, start, end')

class Corpus(OrderedDict):
    def characters(self):
        return sum([ len(data) for (_, data) in self.values() ])

    def documents(self):
        return len(self)

class FragmentedCorpus(list):
    def __init__(self, corpus, block_size=1):
        self.corpus = corpus
        
        remaining = None
        fragments = []
        length = 0
    
        for (docno, doc) in self.corpus.items():
            for (i, j) in self.range_(0, len(doc.data), block_size, remaining):
                f = Fragment(docno, *map(int, [ i, j ]))
                fragments.append(f)
                length += j - i
                assert(length <= block_size)
                
                if length == block_size:
                    self.append(fragments)
                
                    remaining = None
                    fragments = []
                    length = 0

            if fragments:
                remaining = block_size - length

        if fragments:
            self.append(fragments)

    def range_(self, start, stop, step, offset=None):
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
            
    def strings(self, start=0, end=None):
        if end is None:
            end = len(self)

        for i in range(start, len(self)):
            string = []
            for (docno, start, end) in self[i]:
                s = self.corpus[docno].data[start:end]
                string.append(s)
            yield ''.join(string)

    def at(self, i):
        return self.strings(i, i + 1)
