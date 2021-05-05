import numpy as np
from umap import UMAP

from logic.reduction.reducer import Reducer


class UmapReducer(Reducer):
    def __init__(self, dim_start, dim_end, min_dist, n_neighbors):
        self.dim_start = dim_start
        self.dim_end = dim_end
        self.min_dist = min_dist
        self.n_neighbors = n_neighbors
        self.mapper = None

    def reduce(self, data):
        # Names for the dimensionality reduction fields
        vector_field_name = f'vector_{self.dim_start}_d'
        dimensionality_data = list(map(lambda x: x[vector_field_name], data))

        # Do the dimensionality reduction
        vectors_x_d = self._compute_umap(dimensionality_data)

        # Augment the data with the reduced vector field data
        reduced_vector_field_name = f'vector_{self.dim_end}_d'
        for idx, datum in enumerate(data):
            datum[reduced_vector_field_name] = vectors_x_d[idx].tolist()

        return data

    def get_model_data(self):
        if self.mapper is None:
            raise ValueError('Mapper is null. Make sure reduce is called before accessing data.')

        return self.mapper

    def _compute_umap(self, data):
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
            return np.full((vector_matrix.shape[0], self.dim), 0)

        self.mapper = self._fit(vector_matrix, self.dim, self.min_dist, self.n_neighbors)
        return self._transform(vector_matrix)

    # NB: there is a hard limit that the data must have more than 2 points,
    # otherwise UMAP will fail. UMAP has a limitation on using spectral
    # initialization only when n_components < data.shape.
    # See this issue: https://github.com/lmcinnes/umap/issues/201

    def _fit(self, data):
        if (self.n_components >= data.shape[0] - 1):
            init = 'random'
        else:
            init = 'spectral'

        return UMAP(n_components=self.n_components,
                    min_dist=self.min_dist,
                    n_neighbors=self.n_neighbors,
                    init=init).fit(data)

    def _transform(self, data):
        return self.mapper.transform(data)
