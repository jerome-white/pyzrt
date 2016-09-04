import operator as op
from itertools import combinations, filterfalse

import posting

posting = Posting()
for i in posting.posting.keys():
    if i.frequency() > args.threshold:
        continue

    weight = posting.weight(i)
    equality = lambda x: op.eq(*x)
    for (x, y) in filterfalse(equality, combinations(posting.each(i), 2)):
        dotplot[cell(x)][cell(y)] += weight
