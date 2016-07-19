import segment
import document
import distance

msg = 'text processing vs. speech processing'
d = document.Document(None, None, msg)
c = document.Corpus()
c.append(d)

s = segment.Slicer()
d = distance.CharacterWiseDistance()
dots = c.similarity(s, d)
c.dotplot(dots, 'aren.png')
