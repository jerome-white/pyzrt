from pathlib import Path

from zrtlib import zutils

path = Path('/',
            'Volumes',
            'Stick',
            'wsj',
            '2017_0118_020518',
            'evals--progressive',
            '04',
            'ua',
            'WSJQ00259-0000')

with path.open() as fp:
    for (i, _) in zutils.read_trec(fp, True):
        print(i)
