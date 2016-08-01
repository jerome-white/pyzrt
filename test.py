import segment
import distance
import similarity

corpus = {
    'd1': segment.Document(None, 'text processing vs. speech processing'),
}

segmentation = segment.segment(corpus, 1)
chunks = similarity.chunk(corpus, segmentation, distance.CharacterWiseDistance)
matrix = similarity.similarity(chunks)
dots = similarity.to_numpy(matrix)
similarity.dotplot(dots, 'test.png')
