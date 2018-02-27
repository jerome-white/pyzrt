from pathlib import Path
from argparse import ArgumentParser

import pyzrt as pz

arguments = ArgumentParser()
arguments.add_argument('--document', type=Path)
arguments.add_argument('--number', type=int)
arguments.add_argument('--model', default='ua')
args = arguments.parse_args()

log = pz.util.get_logger(True)
log.info('{0} {1}'.format(args.document, args.model))

terms = pz.TermCollection(args.document)
query = pz.Query(terms, args.model, args.number)
print(query)
