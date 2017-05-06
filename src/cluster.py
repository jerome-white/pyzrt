from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

from zrtlib import cluster
from zrtlib.indri import QueryDoc

arguments = ArgumentParser()
arguments.add_argument('--plot', type=Path)
arguments.add_argument('--save', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--existing', type=Path)
arguments.add_argument('--documents', type=Path)
args = arguments.parse_args()

documents = itertools.filterfalse(QueryDoc.isquery, args.documents.iterdir())
cluster = KMeans(documents, n_cluster=50)
cluster.write(args.output)
if args.plot:
    cluster.plot(args.plot)
