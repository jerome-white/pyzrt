import segment
import distance
import similarity

corpus = {
    'd1': segment.Document(None, 'text processing vs. speech processing'),
}

segmentation = segment.segment(corpus)
chunks = similarity.chunk(corpus, segmentation)
matrix = similarity.similarity(chunks, distance.characters)
dots = similarity.to_numpy(matrix)
similarity.dotplot(dots, 'test.png')
