import sys
import csv
import dots

from argparse import ArgumentParser

arguments = ArgumentParser()
arguments.add_argument('--png')
args = arguments.parse_args()

reader = csv.reader(sys.stdin)
d = {}
for (*key, value) in reader:
    k = tuple(map(int, key))
    d[k] = float(value)

pixels = dots.to_numpy(d)
dots.dotplot(pixels, args.png)
    
