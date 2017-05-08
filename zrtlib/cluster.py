import csv
import operator as op
import collections
from pathlib import Path
from functools import singledispatch
from multiprocessing import Pool

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn import cluster
from sklearn.feature_extraction.text import TfidfTransformer

from zrtlib import logger
from zrtlib.document import TermDocument

Entry = collections.namedtuple('Entry', 'type, cluster, value')

def toframe(path):
    log = logger.getlogger()
    log.info(path.stem)

    document = TermDocument(path)
    counts = document.df['term'].value_counts()
    transform = lambda x: document.name

    return pd.DataFrame.from_dict([ counts.to_dict() ]).rename(transform)

@singledispatch
def getdocs(documents):
    with Pool() as pool:
        return pd.concat(pool.imap_unordered(toframe, documents)).fillna(0)

@getdocs.register(Path)
def _(documents):
    return pd.read_csv(documents)

class Cluster:
    def __init__(self, documents, save_raw_to=None):
        df = getdocs(documents)
        if save_raw_to is not None:
            df.to_csv(save_raw_to)

        self.labels = df.index
        self.features = df.columns
        self.observations = TfidfTransformer().fit_transform(df.values)

class Centroid(Cluster):
    def __init__(self, documents):
        super().__init__(documents)

        self.model = self.get_model()
        self.model.fit(self.observations)

    def get_model(self):
        raise NotImplementedError()

    def plot(self, output):
        plt.clf()
        self.visualize()
        plt.savefig(str(output))

    def visualize(self):
        raise NotImplementedError()

    def write(self, fp, n_terms=0):
        writer = csv.DictWriter(fp, fieldnames=Entry._fields)
        writer.writeheader()
        writer.writerows(map(Entry._asdict, self.get_entries(n_terms)))

    def get_entries(self, n_terms):
        raise NotImplementedError()

class KMeans(Centroid):
    def get_model(self):
        return cluster.KMeans(n_clusters=50, n_jobs=-1)

    def get_entries(self, n_terms):
        #
        # documents
        #
        for i in zip(self.labels, self.model.labels_):
            yield Entry('document', *i)

        #
        # terms
        #
        if n_terms > 0:
            order_centroids = self.model.cluster_centers_.argsort()[:, ::-1]
            for i in range(self.model.n_clusters):
                for j in order_centroids[i,:n_terms]:
                    yield Entry('term', i, self.features[i])

    def elbow(self, output):
        raise NotImplementedError()

class DBScan(Centroid):
    def get_model(self):
        return cluster.DBSCAN(n_jobs=-1)

    # http://scikit-learn.org/stable/auto_examples/cluster/plot_dbscan.html
    def visualize(self):
        core_samples_mask = np.zeros_like(self.model.labels_, dtype=bool)
        core_samples_mask[self.model.core_sample_indices_] = True

        unique_labels = set(self.model.labels_)
        colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_labels)))

        markers = { 'marker': 'o', 'markeredgecolor': 'k' }

        for (k, col) in zip(unique_labels, colors):
            # black used for noise
            markers['markerfacecolor'] = 'k' if k == -1 else col

            class_member_mask = (self.model.labels_ == k)

            for (f, m) in zip((np.array, np.invert), (14, 6)):
                mask = f(core_samples_mask)
                xy = self.observations[class_member_mask & mask]
                plt.plot(xy[:, 0], xy[:, 1], markersize=m, **markers)

        noise = 1 if -1 in self.model.labels_ else 0
        n_clusters_ = len(set(self.model.labels_)) - noise
        plt.title('Estimated number of clusters: {0}'.format(n_clusters_))
