from umap import UMAP


def fit(data, n_components=2):
    return UMAP(n_components=n_components, min_dist=0.01).fit(data)  # TODO: Confirm these parameters are correct


def transform(mapper, data):
    return mapper.transform(data)
