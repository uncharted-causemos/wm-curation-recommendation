import hdbscan
import pandas as pd
import numpy as np


def compute_clusters(data, min_cluster_size, min_samples, cluster_selection_epsilon):
    print('Computing cluster ids for all factors')
    try:
        clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size,
                                    min_samples=min_samples,
                                    cluster_selection_epsilon=cluster_selection_epsilon)
        cluster_ids = clusterer.fit_predict(data)
    except Exception as e:
        print('ERROR: There was an exception while trying to compute clusters')
        print('Exception Details: ', e)
        return _noisy_cluster_ids(data)
    print('Finished computing cluster ids for all factors')
    return cluster_ids


def _noisy_cluster_ids(data):
    return np.full(data.shape[0], -1)
