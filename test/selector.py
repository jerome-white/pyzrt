from pathlib import Path

import pandas as pd

from zrtlib.document import TermDocument, HiddenDocument
from zrtlib.selector.strategy import BlindHomogenous
from zrtlib.selector.management import TermSelector
from zrtlib.selector.technique import Random

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

ts = TermSelector(BlindHomogenous(Random))
for i in docs:
    ts.add(TermDocument(i))

if __name__ == '__main__':
    query = HiddenDocument(path.joinpath('WSJQ00298-0000'))
    for i in ts:
        assert(i in query.df[HiddenDocument.columns['visible']].values)
        f = query.flip(i)
        print(i, f)
else:
    df = pd.concat(ts.documents.values(), copy=False)
    df.reset_index(drop=True, inplace=True)
