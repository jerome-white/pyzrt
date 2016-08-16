import sys
import csv
import logger

import operator as op
import multiprocessing as mp

from corpus import to_string
from pathlib import Path
from itertools import islice
from collections import namedtuple

Args = namedtuple('Args', 'anchor, corpus, fragments, distance')
Fragment = namedtuple('Fragment', 'docno, start, end')

def func(args):
    log = logger.getlogger()
    log.info(args.anchor)
    
    s1 = None
    writer = csv.writer(sys.stdout)

    g = lambda x: to_string(args.corpus, x)
    f = islice(args.fragments, args.anchor, None)
    for (i, s2) in enumerate(map(g, f), args.anchor):
        if s1 is None:
            s1 = s2
        else:
            d = args.distance(s1, s2)
            writer.writerow([ args.anchor, i, float(d) ])
            
def enum(corpus, fragments, distance):
    for (i, _) in enumerate(fragments):
        yield Args(i, corpus, fragments, distance)
        
def pairs(corpus_directory, fragment_file, distance=op.eq):
    log = logger.getlogger(True)
    
    with mp.Manager() as manager:
        log.info('+ corpus')
        path = Path(corpus_directory)
        corpus = manager.dict()
        for i in path.iterdir():
            with i.open() as fp:
                corpus[i.name] = fp.read()
        log.info('- corpus {0}'.format(len(corpus)))

        log.info('+ fragments')
        frames = []
        previous = None
        fragments = manager.list()
        with open(fragment_file) as fp:
            reader = csv.reader(fp)
            for row in reader:
                (current, key) = map(int, row[:2])
                
                if previous is not None and previous != current:
                    frames.sort(key=op.itemgetter(0))
                    fragments.extend([ x[1:] for x in frames ])
                    frames = []
                    
                fragment = Fragment(row[2], *map(int, row[3:]))
                frames.append([ key, fragment ])
                previous = current
        log.info('- fragments {0}'.format(len(fragments)))

        log.info('+ similarity')
        with mp.Pool() as pool:
            iterable = enum(corpus, fragments, distance)
            for _ in pool.imap_unordered(func, iterable):
                pass
        log.info('- similarity')
