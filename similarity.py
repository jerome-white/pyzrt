import sys
import csv
import logger
import corpus

import operator as op

from collections import namedtuple
from multiprocessing import Pool

Args = namedtuple('Args', 'anchor, offset, corpus, fragment_file, distance')
Fragment = namedtuple('Fragment', 'docno, start, end')

def f(args):
    s1 = None
    frames = []
    previous = args.anchor
    peel = op.itemgetter(1)
    writer = csv.writer(sys.stdout)
    log = logger.getlogger()
    
    with open(args.fragment_file) as fp:
        fp.seek(args.offset)
        reader = csv.reader(fp)
        for row in reader:
            (current, key) = [ int(x) for x in row[:2] ]
            fragment = Fragment(row[2], *map(int, row[3:]))
            
            if current != previous:
                frames.sort(key=op.itemgetter(0))
                string = corpus.to_string(map(peel, frames), args.corpus)
                
                if s1:
                    d = args.distance(s1, string)
                    writer.writerow([ args.anchor, previous, float(d) ])
                else:
                    s1 = string
                    
                frames = []
            frames.append([ key, fragment ])
            previous = current
            
def enum(corpus, fragment_file, distance):
    offset = 0
    previous = None
    
    with open(fragment_file) as fp:
        for line in fp:
            (current, _) = line.split(',', 1)
            if previous is None or current != previous:
                yield Args(current, offset, corpus, fragment_file, distance)
            previous = current
            offset += len(line) + 1
            
def pairs(corpus, fragment_file, distance=op.eq):
    with Pool() as pool:
        for _ in pool.imap_unordered(f, enum(corpus, fragment_file, distance)):
            pass
