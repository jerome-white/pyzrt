import document

from segment import Slicer as segment_
from distance import CharacterWiseDistance as distance_

msg = 'text processing vs. speech processing'
d = document.Document(None, None, msg)
c = document.Corpus()
c.append(d)

s = segment_(distance_)
dots = c.similarity(s, parallel=4)
c.dotplot(dots, 'test.png')
