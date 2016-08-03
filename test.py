import distance
import similarity

from corpus import Corpus, Document

corpus = Corpus()
corpus['d1'] = Document(None, 'text processing vs. speech processing')

matrix = similarity.similarity(corpus.mend(corpus.fragment()))
dots = similarity.to_numpy(matrix)
similarity.dotplot(dots, 'test.png')
