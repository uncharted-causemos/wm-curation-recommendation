from umap import UMAP


def fit(data, n_components=2):
    return UMAP(n_components=2).fit(data)


def transform(mapper, data):
    return mapper.transform(data)
