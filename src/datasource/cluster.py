import hdbscan
import numpy as np

from datasource.knowledge_base import KnowledgeBase
from datasource.utils import full


def compute_clusters(self, data, dim, min_cluster_size, min_samples, epsilon):
    # Need to pass in only the 'vector_x_d' field of the data to
    # the HDBSCAN clusterer
    vector_field_name = f'vector_{dim}_d'
    cluster_data = np.array(list(map(lambda x: x[vector_field_name], data)))

    # Computer the clusters
    clusters = None
    try:
        clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size,
                                    min_samples=min_samples,
                                    cluster_selection_epsilon=epsilon)
        clusters = clusterer.fit_predict(cluster_data)
    except Exception:
        clusters = full(cluster_data.shape[0], -1)

    # Augment the data passed in with the 'cluster_id' field
    for idx, datum in enumerate(data):
        datum['cluster_id'] = clusters[idx].item()

    return data


KnowledgeBase.compute_clusters = compute_clusters
