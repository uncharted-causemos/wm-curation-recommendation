from umap import UMAP


def fit(data, n_components, min_dist):
    return UMAP(n_components=n_components, min_dist=min_dist).fit(data)  # TODO: Confirm these parameters are correct


def transform(mapper, data):
    return mapper.transform(data)
