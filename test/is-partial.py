from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

from zrtlib import logger

def ispartial(path):
    df = TermDocument(path).df
    partials = df[df['ngram'].str.len() != df['length']]

    return (path, not partials.empty)

def walk(path):
    for i in path.iterdir():
        if not i.is_dir():
            yield i
        else:
            yield from walk(i)

arguments = ArgumentParser()
arguments.add_argument('--directory', type=Path)
args = arguments.parse_args()

log = logger.getlogger()

with Pool() as pool:
    for (path, result) in pool.imap_unordered(ispartial, walk(args.directory)):
        if result:
            log.info(path)
            break
    else:
        log.info('complete')
