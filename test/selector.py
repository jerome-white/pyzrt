from pathlib import Path

import pandas as pd

from zrtlib.document import TermDocument, HiddenDocument
from zrtlib.selector.strategy import BlindHomogenous
from zrtlib.selector.management import TermSelector
import zrtlib.selector.technique as tech

path = Path('/',
            'Volumes',
            'Elements',
            'NYU',
            'Research',
            'pyzrt',
            'wsj',
            '2017_0118_020518',
            'pseudoterms',
            '07')
docs = [ path.joinpath('WSJ900402-00' + str(x)) for x in range(17, 20) ]

ts = TermSelector(BlindHomogenous(tech.Entropy))
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
