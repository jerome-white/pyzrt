import itertools
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

from zrtlib import logger
from zrtlib import cluster
from zrtlib.indri import QueryDoc
from zrtlib.cluster import KMeans

arguments = ArgumentParser()
arguments.add_argument('--plot', type=Path)
arguments.add_argument('--save', type=Path)
arguments.add_argument('--existing', type=Path)
arguments.add_argument('--input', type=Path)
arguments.add_argument('--output', type=Path)
args = arguments.parse_args()

log = logger.getlogger()

if args.existing:
    documents = args.existing
    save = None
else:
    documents = itertools.filterfalse(QueryDoc.isquery, args.input.iterdir())
    save = args.save

cluster = KMeans(documents, save)

log.info('Begin processing')

with args.output.open('w', buffering=1) as fp:
    cluster.write(fp)
# if args.plot:
#     cluster.visualize(args.plot)
