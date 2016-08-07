import distance

from corpus import Corpus, Document
from similarity import RowPerCPU as Similarity

corpus = Corpus()
corpus['d1'] = Document(None, 'text processing vs. speech processing')

s = Similarity()
matrix = s.similarity(corpus.mend(corpus.fragment()))
dots = s.to_numpy(matrix)
s.dotplot(dots, 'test.png')
