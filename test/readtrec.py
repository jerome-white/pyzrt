from pathlib import Path

from zrtlib import zutils

with p.open() as fp:                                                    
    for (i, _) in zutils.read_trec(fp):
        print(i)
