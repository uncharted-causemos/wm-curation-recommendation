from umap import UMAP


def fit(data, n_components, min_dist):
    # Note, there is a hard limit that the data must have more than 2 points, otherwise UMAP will fail.

    # UMAP has a limitation on using spectral initialization only when n_components < data.shape
    # See this issue: https://github.com/lmcinnes/umap/issues/201
    if (n_components >= data.shape[0] - 1):
        init = 'random'
    else:
        init = 'spectral'
    return UMAP(n_components=n_components, min_dist=min_dist, init=init).fit(data)


def transform(mapper, data):
    return mapper.transform(data)
