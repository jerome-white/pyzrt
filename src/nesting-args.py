import random
from pathlib import Path
from argparse import ArgumentParser
from itertools import filterfalse

from zrtlib.indri import QueryDoc

class TermFiles(list):
    def add(self, path):
        self.append(str(path))

    def __str__(self):
        opt = ' --term-file '
        return opt + opt.join(self)

def enum(path, sample=None):
    if sample is None:
        for i in path.glob('**/WSJ*'):
            if not QueryDoc.isquery(i):
                yield i.stem
    else:
        yield from random.sample(list(enum(path)), sample)

arguments = ArgumentParser()
arguments.add_argument('--pseudoterms', type=Path)
arguments.add_argument('--sample', type=int)
arguments.add_argument('--n-grams')
args = arguments.parse_args()

if args.n_grams:
    rng = map(int, args.n_grams.split(':'))
    ngrams = range(*rng)
else:
    ngrams = None
    
for i in enum(args.pseudoterms, args.sample):
    terms = TermFiles()
    for j in args.pseudoterms.iterdir():
        if not ngrams or int(j.stem) in ngrams:
            path = j.joinpath(i)
            assert(path.exists())
            terms.add(path)
    print(terms)
