import sys
import csv
import dots

from argparse import ArgumentParser

arguments = ArgumentParser()
arguments.add_argument('--png')
args = arguments.parse_args()

d = {}
for (*key, value) in csv.reader(sys.stdin):
    k = tuple(map(int, key))
    d[k] = float(value)

pixels = dots.to_numpy(d)
dots.dotplot(pixels, args.png)
    
