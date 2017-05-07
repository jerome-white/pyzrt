import csv
import operator as op
import collections
from multiprocessing import Pool

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn import cluster
from sklearn.feature_extraction.text import TfidfTransformer

from zrtlib.document import TermDocument

Entry = collections.namedtuple('Entry', 'type, cluster, value')

def getdocs(path):
    document = TermDocument(path)
    counts = document.df['term'].value_counts()
    transform = lambda x: document.name

    return pd.DataFrame.from_dict([ counts.to_dict() ]).rename(transform)

class Cluster:
    def __init__(self, documents):
        if documents.is_dir():
            with Pool() as pool:
                df = pd.concat(pool.imap_unordered(getdocs, documents))
            df.fillna(0, inplace=True)
        else:
            df = pd.read_csv(documents)
        self.labels = df.index.values
        self.observations = TfidfTransformer().fit_transform(df.values)

class Centroid(Cluster):
    def __init__(self, documents, **kwargs):
        super().__init__(documents)

        self.model = self.mkmodel(**kwargs)
        self.model.fit(self.observations)

    def mkmodel(self, **kwargs):
        raise NotImplementedError()

    def visualize(self, output):
        plt.clf()
        self.visualize_()
        plt.savefig(str(output))

    def visualize_(self):
        raise NotImplementedError()

    def write(self, fp, n_terms=10):
        writer = csv.DictWriter(fp, fieldnames=Entry._fields)
        writer.writeheader()
        writer.writerows(map(op.methodcaller('_asdict'), self.extract()))

class KMeans(Centroid):
    def mkmodel(self, **kwargs):
        return cluster.KMeans(**kwargs)

    def visualize_(self):
        raise NotImplementedError()

    def elbow(self, output):
        raise NotImplementedError()

    def write(self, fp, n_terms=0):
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
            terms = self.observations.get_feature_names()

            for i in range(self.model.n_clusters):
                for j in order_centroids[i,:n_terms]:
                    yield Entry('term', i, terms[i])

class DBScan(Centroid):
    def mkmodel(self, **kwargs):
        return cluster.DBSCAN(**kwargs)

    # http://scikit-learn.org/stable/auto_examples/cluster/plot_dbscan.html
    def visualize_(self):
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
