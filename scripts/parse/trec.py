import sys
import csv
from pathlib import Path
from argparse import ArgumentParser

import pyzrt as pz

arguments = ArgumentParser()
arguments.add_argument('--model')
arguments.add_argument('--query', type=Path)
arguments.add_argument('--ngrams', type=int)
args = arguments.parse_args()

log = pz.util.get_logger(True)
log.info(' '.join(map(str, (args.model, args.query, args.ngrams))))

writer = None
results = {
    'model': args.model,
    'query': args.query,
    'ngrams': args.ngrams,
}

for i in pz.Search.interpret(sys.stdin):
    results.update(i.results)
    if writer is None:
        writer = csv.DictWriter(sys.stdout, fieldnames=results.keys())
        writer.writeheader()
    writer.writerow(results)
