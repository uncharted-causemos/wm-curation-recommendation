import numpy as np

from datasource.knowledge_base import KnowledgeBase
from datasource.utils import full

from umap import UMAP


# NB: there is a hard limit that the data must have more than 2 points,
# otherwise UMAP will fail. UMAP has a limitation on using spectral
# initialization only when n_components < data.shape.
# See this issue: https://github.com/lmcinnes/umap/issues/201
def _fit(data, n_components, min_dist, n_neighbors):
    if (n_components >= data.shape[0] - 1):
        init = 'random'
    else:
        init = 'spectral'

    return UMAP(n_components=n_components,
                min_dist=min_dist,
                n_neighbors=n_neighbors,
                init=init).fit(data)


def _transform(data, mapper):
    return mapper.transform(data)


def _compute_umap(data, dim, min_dist, n_neighbors):
    """
    UMAP can't run with n_neighbors < 2, and UMAP forces n_neighbors =
    min(n_neighbors, data.shape[0] - 1). This allows for easy testing on small
    indicies if need be without constantly throwing errors to the caller. It's
    assumed that any valuable data transformations will always have a data size
    larger than the nominal values of n_neighbors~=15. In this way, we'll still
    be able to generate recommendations and the rest of CauseMos can continue
    to be tested.
    """
    vector_matrix = np.array(data)

    if vector_matrix.shape[0] - 1 < 2:
        return full((vector_matrix.shape[0], dim), 0)

    mapper = _fit(vector_matrix, dim, min_dist, n_neighbors)
    return _transform(vector_matrix, mapper)


def compute_umap(self, data, dim_start, dim_end, min_dist, n_neighbors):
    # Names for the dimensionality reduction fields
    vector_field_name = f'vector_{dim_start}_d'
    dimensionality_data = list(map(lambda x: x[vector_field_name], data))

    # Do the dimensionality reduction
    vectors_x_d = _compute_umap(
        dimensionality_data, dim_end, min_dist, n_neighbors)

    # Augment the data with the reduced vector field data
    reduced_vector_field_name = f'vector_{dim_end}_d'
    for idx, datum in enumerate(data):
        datum[reduced_vector_field_name] = vectors_x_d[idx].tolist()

    return data


KnowledgeBase.compute_umap = compute_umap
