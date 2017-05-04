import csv
import itertools
import matplotlib.pyplot as plt
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

import numpy as np
import pandas as pd
from sklearn.cluster import dbscan as Cluster

from zrtlib.indri import QueryDoc
from zrtlib.document import TermDocument

def func(path):
    document = TermDocument(path)
    counts = document.df['term'].value_counts()
    transform = lambda x: document.name

    return pd.DataFrame.from_dict([ counts.to_dict() ]).rename(transform)

arguments = ArgumentParser()
arguments.add_argument('--plot', type=Path)
arguments.add_argument('--save', type=Path)
arguments.add_argument('--output', type=Path)
arguments.add_argument('--existing', type=Path)
arguments.add_argument('--documents', type=Path)
args = arguments.parse_args()

#
# Create the document matrix
#
if args.existing and args.existing.exists():
    df = pd.read_csv(args.existing)
else:
    with Pool() as pool:
        itr = itertools.filterfalse(QueryDoc.isquery, args.documents.iterdir())
        df = pd.concat(pool.imap_unordered(func, itr))
    df.fillna(0, inplace=True)
    if args.save:
        with args.save('w') as fp:
            df.to_csv(fp)

#
# Cluster the matrix
#
cluster = Cluster(df.values)
with args.output.open('w') as fp:
    fieldnames = [ 'document', 'cluster' ]
    writer = csv.DictWriter(fp, fieldnames=fieldnames)
    writer.writeheader()
    for i in zip(df.index, cluster.labels_):
        writer.writerow(dict(zip(fieldnames, i)))

if args.plot:
    # http://scikit-learn.org/stable/auto_examples/cluster/plot_dbscan.html

    core_samples_mask = np.zeros_like(cluster.labels_, dtype=bool)
    core_samples_mask[cluster.core_sample_indices_] = True

    unique_labels = set(cluster.labels_)
    colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_labels)))
    for (k, col) in zip(unique_labels, colors):
        markerfacecolor = 'k' if k == -1 else col # black used for noise.
        class_member_mask = (cluster.labels_ == k)

        xy = df.values[class_member_mask & core_samples_mask]
        plt.plot(xy[:, 0], xy[:, 1],
                 marker='o',
                 markerfacecolor=markerfacecolor,
                 markeredgecolor='k',
                 markersize=14)

        xy = df.values[class_member_mask & ~core_samples_mask]
        plt.plot(xy[:, 0], xy[:, 1],
                 marker='o',
                 markerfacecolor=markerfacecolor,
                 markeredgecolor='k',
                 markersize=6)

    noise = 1 if -1 in cluster.labels_ else 0
    n_clusters_ = len(set(cluster.labels_)) - noise
    plt.title('Estimated number of clusters: {0}'.format(n_clusters_))
    plt.savefig(str(args.plot))