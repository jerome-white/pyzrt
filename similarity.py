import sys
import csv
import logger
import corpus

import operator as op

from collections import namedtuple
from multiprocessing import Pool

Args = namedtuple('Args', 'anchor, offset, corpus, fragment_file, distance')
Fragment = namedtuple('Fragment', 'docno, start, end')

def mkfragments(fragment_file, offset=0):
    frames = []
    previous = None
    
    with open(fragment_file) as fp:
        fp.seek(offset)
        reader = csv.reader(fp)
        for row in reader:
            (current, key) = [ int(x) for x in row[:2] ]
            fragment = Fragment(row[2], *map(int, row[3:]))
            
            if previous is not None and previous != current:
                frames.sort(key=op.itemgetter(0))
                yield (previous, map(op.itemgetter(1), frames))
                frames = []
                
            frames.append([ key, fragment ])
            previous = current

def f(args):
    s1 = None
    writer = csv.writer(sys.stdout)
    
    for (i, fragment) in mkfragments(args.fragment_file, args.offset):
        s2 = corpus.to_string(args.corpus, fragment)
        if i == args.anchor:
            assert(s1 is None)
            s1 = s2
        else:
            d = float(args.distance(s1, s2))
            writer.writerow([ args.anchor, i, d ])
            
def enum(corpus, fragment_file, distance):
    offset = 0
    previous = None
    
    with open(fragment_file) as fp:
        for line in fp:
            current = int(line.split(',', 1).pop(0))
            if previous is None or previous != current:
                yield Args(current, offset, corpus, fragment_file, distance)
            previous = current
            offset += len(line) + 1
            
def pairs(corpus, fragment_file, distance=op.eq):
    with Pool() as pool:
        for _ in pool.imap_unordered(f, enum(corpus, fragment_file, distance)):
            pass
