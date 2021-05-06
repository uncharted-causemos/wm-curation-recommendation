

import hdbscan
import numpy as np

from logic.clustering.clusterer import Clusterer


class HDBScanClusterer(Clusterer):
    def __init__(self, dim, min_cluster_size, min_samples, epsilon):
        self.dim = dim
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.epsilon = epsilon
        self.clusterer = None

    def cluster(self, data):
        # Need to pass in only the 'vector_x_d' field of the data to
        # the HDBSCAN clusterer
        vector_field_name = f'vector_{self.dim}_d'
        cluster_data = np.array(list(map(lambda x: x[vector_field_name], data)))

        # Computer the clusters
        clusters = None
        try:
            clusterer = hdbscan.HDBSCAN(min_cluster_size=self.min_cluster_size,
                                        min_samples=self.min_samples,
                                        cluster_selection_epsilon=self.epsilon)
            clusters = clusterer.fit_predict(cluster_data)
        except Exception:
            clusters = np.full(cluster_data.shape[0], -1)

        # Augment the data passed in with the 'cluster_id' field
        for idx, datum in enumerate(data):
            datum['cluster_id'] = clusters[idx].item()

        return data

    def get_model_data(self):
        if self.clusterer is None:
            raise ValueError('Clusterer is empty. Make usre cluster is called before accessing model data.')

        return self.clusterer
