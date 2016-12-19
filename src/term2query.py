import multiprocessing as mp

from pathlib import Path
from argparse import ArgumentParser

from zrtlib import query
from zrtlib import zutils
from zrtlib import logger

def func(args):
    (terms, model, output) = args
    
    log = logger.getlogger()
    log.info(terms.stem)

    models_ = {
        'ua': (query.BagOfWords, {}),
        'sa': (query.Synonym, {}),
        'u1': (query.Synonym, {
            'longest': 1,
        }),
        'un': (query.ShortestPath, {
            'partials': False,
        }),
        'uaw': (query.TotalWeight, {}),
        'saw': (query.LongestWeight, {}),
    }

    (Model, kwargs) = models_[model]
    q = Model(terms, **kwargs)
    with output.joinpath(terms.stem).open('w') as fp:
        fp.write(str(q))
    
arguments = ArgumentParser()
arguments.add_argument('--model')
arguments.add_argument('--input', type=Path)
arguments.add_argument('--output', type=Path)
args = arguments.parse_args()

with mp.Pool() as pool:
    f = lambda x: (x, args.model.lower(), args.output)
    for _ in pool.imap(func, map(f, zutils.walk(args.input))):
        pass
