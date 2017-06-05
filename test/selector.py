import sys
from pathlib import Path

import pandas as pd

from zrtlib.document import TermDocument, HiddenDocument
from zrtlib.selector.feedback import RecentWeighted
from zrtlib.selector.strategy import BlindHomogenous
from zrtlib.selector.management import TermSelector
import zrtlib.selector.technique as tq

location = sys.argv[1] if len(sys.argv) > 1 else '.'

WSJ = 'WSJ'
docs = []
for p in Path(location).iterdir():
    if p.stem[:len(WSJ)] == WSJ:
        print(p)
        docs.append(p)

ts = TermSelector(BlindHomogenous(tq.Entropy), RecentWeighted())
for i in docs:
    ts.add(TermDocument(i))

if __name__ == '__main__':
    # query = HiddenDocument(path.joinpath('WSJQ00298-0000'))
    # for i in ts:
    #     assert(i in query.df[HiddenDocument.columns['visible']].values)
    #     f = query.flip(i)
    #     print(i, f)
    s = set()
    for i in ts:
        assert(i not in s)
        print(i)
        s.add(i)
else:
    df = pd.concat(ts.documents.values(), copy=False)
    df.reset_index(drop=True, inplace=True)
