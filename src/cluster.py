import itertools
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

from zrtlib import cluster
from zrtlib.indri import QueryDoc
from zrtlib.cluster import KMeans

arguments = ArgumentParser()
# arguments.add_argument('--plot', type=Path)
# arguments.add_argument('--save', type=Path)
# arguments.add_argument('--existing', type=Path)
arguments.add_argument('--input', type=Path)
arguments.add_argument('--output', type=Path)
args = arguments.parse_args()

documents = itertools.filterfalse(QueryDoc.isquery, args.input.iterdir())
cluster = KMeans(documents, n_cluster=50, n_jobs=-1)
with args.output.open('w', buffering=1) as fp:
    cluster.write(fp)
# if args.plot:
#     cluster.visualize(args.plot)
