import collections
import operator as op

import corpus
import similarity

IndexedFragment = collections.namedtuple('IndexedFragment',
                                         [ 'index' ] + list(Fragment._fields))

class Posting:
    def __init__(self, fragment_file, corpus_directory=None):
        self.posting = collections.defaultdict(list)

        if corpus_directory:
            corpus_ = dict(corpus.from_disk(corpus_directory))
        else:
            corpus_ = None
            
        for (i, fragment) in enumerate(similarity.frag(fragment_file)):
            token = to_string(fragment, corpus_, corpus_directory)
            value = IndexedFragment(i, *fragment)
            self.posting[token].append(value)
    
    def frequency(self, token):
        return len(self.posting[token]) if token in self.posting else 0

    def weight(self, token):
        freq = self.frequency(token)
        keys = set(self.postings.keys())
        
        n = max(map(self.frequency, keys.difference([ token ])))

        return freq / n

    def each(self, index):
        yield from map(op.itemgetter(-1), self[index])
