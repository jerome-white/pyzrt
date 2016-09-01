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

def frag(fragment_file, offset=0):
    frames = []
    previous = None
    peel = lambda x: yield y.pop() for y in sorted(x, key=op.itemgetter(0))
    
    with open(fragment_file) as fp:
        fp.seek(offset)
        for row in csv.reader(fp):
            (current, key) = map(int, row[:2])
                
            if previous is not None and previous != current:
                yield (previous, peel(frames))
                frames = []
                    
            fragment = Fragment(row[2], *map(int, row[3:]))
            frames.append([ key, fragment ])
            previous = current
            
        # since the last line of the file doesn't get included
        if frames:
            yield peel(frames)
    
def func(args):
    log = logger.getlogger()
    log.info(args.anchor)

    corpus = {}
    path = Path(args.corpus_directory)
    for i in path.iterdir():
        with i.open() as fp:
            corpus[i.name] = fp.read()
    log.debug('- corpus {0}'.format(len(corpus)))
    
    s1 = None
    writer = csv.writer(sys.stdout)

    for (i, fragment) in frag(args.fragment_file, args.offset):
        s2 = to_string(corpus, fragment)
        if s1 is None:
            s1 = s2
        else:
            d = args.distance(s1, s2)
            writer.writerow([ args.anchor, i, float(d) ])
            
def enum(corpus_directory, fragment_file, distance):
    offset = 0
    previous = None

    with open(fragment_file) as fp:
        for line in fp:
            current = int(line.split(',', 1).pop(0))
            if previous is None or previous != current:
                yield Args(current, offset, corpus_directory, fragment_file,
                           distance)
                
            previous = current
            offset += len(line) + 1
        
def pairs(corpus_directory, fragment_file, distance=op.eq):
    with mp.Pool() as pool:
        iterable = enum(corpus, fragments, distance)
        for _ in pool.imap_unordered(func, iterable):
            pass
