import hdbscan
import pandas as pd
import numpy as np


def compute_clusters(concept_name, factors):
    print("Computing cluster ids for concept {}".format(concept_name))
    factor_df = _build_factor_df(factors)
    factor_df = _dedupe_factors(factor_df)
    cluster_ids = _compute_cluster_ids(concept_name, factor_df)
    factor_df['cluster_id'] = cluster_ids
    print("Finished computing cluster ids for concept {}".format(concept_name))
    return factor_df


def _compute_cluster_ids(concept_name, factor_df):
    data = np.asarray(factor_df['factor_vector_2_d'].tolist())
    try:
        if data.shape[0] < 20:
            return _noisy_cluster_ids(data)
        clusterer = hdbscan.HDBSCAN(min_cluster_size=20)
        cluster_ids = clusterer.fit_predict(data)
    except Exception as e:
        print("ERROR: There was an exception while trying to compute clusters for concept: {}".format(concept_name))
        print("Exception Details: ", e)
        return _noisy_cluster_ids(data)
    return cluster_ids


def _noisy_cluster_ids(data):
    return np.full(data.shape[0], -1)


def _dedupe_factors(factor_df):
    deduped_factor_df = factor_df.groupby("factor_cleaned", as_index=True).agg({
        "factor_vector_2_d": lambda x: x.iloc[0],
        "id": sum
    })
    return deduped_factor_df


def _build_factor_df(results):
    factor_vectors_2_d = []
    factors_cleaned = []
    ids = []
    for res in results:
        factor_vectors_2_d.append(res["_source"]["factor_vector_2_d"])
        factors_cleaned.append(res["_source"]["factor_cleaned"])
        ids.append([res["_id"]])

    return pd.DataFrame({
        "factor_vector_2_d": factor_vectors_2_d,
        "factor_cleaned": factors_cleaned,
        "id": ids
    })
