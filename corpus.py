# import logger

import numpy as np

from collections import namedtuple, OrderedDict

Document = namedtuple('Document', 'fpath, data')
Fragment = namedtuple('Segment', 'docno, start, end')

# class Fragment(list):
#     def __init__(self, corpus):
#         self.corpus = corpus
        
#     def __str__(self):
#         s = []
#         for (docno, start, end) in i:
#             s = self.corpus[docno].data[start:end]
#             string.append(s)
            
#         return ''.join(s)

class Corpus(OrderedDict):
    def orange(self, start, stop, step, offset=None):
        i = start
        while i < stop:
            if offset is not None:
                j = i + offset
                offset = None
            else:
                j = i + step
            j = min(j, stop)
            
            yield (i, j)
            i = j

    def fragment(self, block_size=1):
        remaining = None
        fragments = []
        length = 0
    
        for (docno, doc) in self.items():
            for (i, j) in self.orange(0, len(doc.data), block_size, remaining):
                f = Fragment(docno, i, j)
                fragments.append(f)
                length += j - i
                
                if length == block_size:
                    yield fragments
                
                    remaining = None
                    fragments = []
                    length = 0

            if fragments:
                remaining = block_size - length

        if fragments:
            yield fragments

    def mend(self, fragments=None):
        for i in fragments:
            string = []
            for (docno, start, end) in i:
                s = self[docno].data[start:end]
                string.append(s)
            yield ''.join(string)
            
    def characters(self):
        return sum([ len(data) for (_, data) in self.values() ])

    def documents(self):
        return len(self)
            
