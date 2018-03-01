#
# Parse trec_eval output (to standard CSV format).
#

import sys
import csv
from argparse import ArgumentParser

import pyzrt as pz

arguments = ArgumentParser()
arguments.add_argument('--topic')
arguments.add_argument('--model', default='indri')
arguments.add_argument('--ngrams', type=int)
args = arguments.parse_args()

log = pz.util.get_logger(True)
log.info(args.topic)

row = {
    'topic': args.topic,
    'model': args.model,
}
writer = None

for i in pz.Search.interpret(sys.stdin):
    row.update(**i.results)
    row['ngrams'] = i.run if args.ngrams is None else i.run

    if writer is None:
        writer = csv.DictWriter(sys.stdout, row.keys())
        writer.writeheader()
    writer.writerow(row)
