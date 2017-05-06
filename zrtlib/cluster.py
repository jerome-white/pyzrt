import csv
from multiprocessing import Pool

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn import cluster
from sklearn.feature_extraction.text import TfidfTransformer

from zrtlib.document import TermDocument

def getdocs(path):
    document = TermDocument(path)
    counts = document.df['term'].value_counts()
    transform = lambda x: document.name

    return pd.DataFrame.from_dict([ counts.to_dict() ]).rename(transform)

class Cluster:
    def __init__(self, documents):
        with Pool() as pool:
            df = pd.concat(pool.imap_unordered(getdocs, documents)).fillna(0)
        self.labels = df.index.values
        self.observations = TfidfTransformer().fit_transform(df.values)

class Centroid(Cluster):
    def __init__(self, documents, **kwargs):
        super().__init__(documents)

        self.model = self.mkmodel(**{ 'n_jobs': -1, **kwargs })
        self.model.fit(self.observations)

    def mkmodel(self, **kwargs):
        raise NotImplementedError()

    def visualize(self, output):
        plt.clf()
        self.visualize_()
        plt.savefig(str(output))

    def visualize_(self):
        raise NotImplementedError()

class KMeans(Centroid):
    def mkmodel(self, **kwargs):
        return cluster.KMeans(**kwargs)

    def visualize_(self):
        raise NotImplementedError()

    def elbow(self, output):
        raise NotImplementedError()

    def write(self, fp, n_terms=10):
        data = []
        keys = [ 'type', 'cluster', 'value' ]

        #
        # terms
        #
        order_centroids = self.model.cluster_centers_.argsort()[:, ::-1]
        terms = self.observations.get_feature_names()

        for i in range(self.model.n_clusters):
            for j in order_centroids[i,:n_terms]:
                data.append(dict(zip(keys, ('term', i, terms[i]))))

        #
        # documents
        #
        for i in zip(self.labels, self.model.labels_):
            data.append(dict(zip(keys, ('document', *i))))

        writer = csv.DictWriter(fp, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

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
