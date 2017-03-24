import csv
from pathlib import Path
from argparse import ArgumentParser

arguments = ArgumentParser()
arguments.add_argument('--metric', action='append')
arguments.add_argument('--input', type=Path)
args = arguments.parse_args()

keys = [ 'guess', 'term' ]
keys.extend(args.metric)

with args.input.open() as fp:
    reader = csv.DictReader(fp)
    for line in reader:
        print(*[ line[x] for x in keys ])
