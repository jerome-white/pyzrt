from pathlib import Path

from zrtlib.document import TermDocument, HiddenDocument
from zrtlib.selector.strategy import SelectionStrategy
from zrtlib.selector.management import TermSelector

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
query = HiddenDocument(path.joinpath('WSJQ00298-0000'))

ts = TermSelector(SelectionStrategy.build('random'))

if __name__ == '__main__':
    kwargs = {
        'query': query,
        'relevant': [ x.stem for x in docs[:2] ],
    }
    ts = TermSelector(SelectionStrategy.build('relevance', **kwargs))

for i in docs:
    ts.add(TermDocument(i))

if __name__ == '__main__':
    for i in ts:
        assert(i in query.df[HiddenDocument.columns['visible']].values)
        f = query.flip(i)
        print(i, f)
