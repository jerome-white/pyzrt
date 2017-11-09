from pathlib import Path
from argparse import ArgumentParser

from zrtlib.terms import TermCollection

def sentences(corpus):
    for i in corpus.iterdir():
        print(i)
        terms = TermCollection(i)
        yield from map(str, terms.regions())

arguments = ArgumentParser()
arguments.add_argument('--corpus', type=Path)
args = arguments.parse_args()

for i in enumerate(sentences(args.corpus)):
    print(*i)
