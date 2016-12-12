import multiprocessing as mp

from pathlib import Path
from argparse import ArgumentParser

from zrtlib import logger
from zrtlib import query

def func(args):
    (terms, model, output) = args
    
    log = logger.getlogger()
    log.info(terms.stem)

    models_ = {
        'ua': query.BagOfWords,
        'sa': query.Clustered,
        'u1': query.Clustered,
        # 'un': None,
        # 'uaw': None,
        # 'saw': None,
    }

    kwargs = {}
    if model == 'sa' or model == 'u1':
        kwargs['indri_operator'] = 'syn'
        if model == 'u1':
            kwargs['retainer'] = query.RetainLongest(1)

    q = models_[model](terms, **kwargs)
    with output.joinpath(terms.stem).open('w') as fp:
        fp.write(str(q))
    
arguments = ArgumentParser()
arguments.add_argument('--model')
arguments.add_argument('--input', type=Path)
arguments.add_argument('--output', type=Path)
args = arguments.parse_args()

with mp.Pool() as pool:
    f = lambda x: (x, args.model.lower(), args.output)
    for _ in pool.imap(func, map(f, args.input.iterdir())):
        pass
