import sys
import csv
from pathlib import Path
from argparse import ArgumentParser

import pyzrt as pz

arguments = ArgumentParser()
arguments.add_argument('--model')
arguments.add_argument('--indri', type=Path)
arguments.add_argument('--index', type=Path)
arguments.add_argument('--qrels', type=Path)
arguments.add_argument('--query', type=Path)
arguments.add_argument('--ngrams', type=int)
arguments.add_argument('--count', type=int, default=1000)
args = arguments.parse_args()

log = pz.util.get_logger(True)
log.info('{0}'.format(args.query.stem))

relevance = pz.QueryRelevance(args.qrels)
search = pz.IndriSearch(args.index, relevance, args.indri)
writer = None

entry = {
    'model': args.model,
    'query': args.query.stem,
    'ngrams': args.ngrams,
}

for i in filter(None, search.do(args.query)):
    entry.update(**i.results)
    if writer is None:
        writer = csv.DictWriter(sys.stdout, fieldnames=entry.keys())
        writer.writeheader()
    writer.writerow(entry)
sys.stdout.flush()
