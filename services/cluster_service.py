import umap
import hdbscan

class ClusterService:
    clusterer = hdbscan.HDBSCAN(min_cluster_size=20)

    def __init__(self):
        