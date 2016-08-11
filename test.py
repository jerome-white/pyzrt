import distance
import similarity as sim

from corpus import Document, Corpus, FragmentedCorpus

documents = [
    ('d1', Document(None, 'text processing vs. speech processing'))
    ]
corpus = Corpus(documents)

fragments = FragmentedCorpus(corpus)
for f in sim.ComparisonPerCPU, sim.RowPerCPU:
    matrix = f(fragments)
    fname = 'test-{0}.png'.format(f.__name__)
    matrix.dotplot(fname)
