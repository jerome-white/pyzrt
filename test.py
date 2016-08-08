import distance

from corpus import Document, Corpus, FragmentedCorpus
from similarity import RowPerCPU as Similarity

documents = [
    ('d1', Document(None, 'text processing vs. speech processing'))
    ]
corpus = Corpus(documents)

fragments = FragmentedCorpus(corpus)
matrix = Similarity(fragments.strings())
matrix.dotplot('test.png')
