import sys
import csv
import logger

import operator as op
import multiprocessing as mp

def pairs(corpus, fragment_file, distance=op.eq, parallel=None):
    if parallel is not None:
        parallel = min(mp.cpu_count(), max(parallel, 1))

    with mp.Pool(parallel) as pool:
        for _ in pool.imap_unordered(f, enum(corpus, fragment_file, distance)):
            pass

def enum(corpus, fragment_file, distance):
    offset = 0
    previous = None
    
    with open(fragment_file) as fp:
        for line in fp:
            current = line.split(',', 1)
            if previous is None or current != previous:
                yield (current, offset, distance, fname)
            previous = current
            offset += len(line)
        
def f(index, offset, distance, corpus, fragments):
    s1 = None
    frames = {}
    previous = index
    peel = itemgetter(1)
    writer = csv.writer(sys.stdout)
    
    with open(fragments) as fp:
        fp.seek(offset)
        reader = csv.reader(fp)
        for row in reader:
            (current, key) = [ int(x) for x in row[:2] ]
            fragment = Fragment(row[1:])
            
            if current != previous:
                frames.sort(key=itemgetter(0))
                string = mkstring(corpus, map(peel, frames))
                
                if s1:
                    d = distance(s1, string)
                    writer.writerow([ index, previous, d ])
                else:
                    s1 = string
                    
                frames = []                    
            frames.append([ key, fragment ])
            previous = current
