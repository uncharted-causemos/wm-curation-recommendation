import numpy as np

from scipy.stats import entropy
from sklearn.neighbors import KDTree


def knn(doc, data, num_recommendations, clustering_dim=20):
    data = np.array(data)
    vector_field_name = f'vector_{clustering_dim}_d'
    vectors = np.array(list(map(lambda x: x[vector_field_name], data)))
    kd_tree = KDTree(vectors, metric='euclidean', leaf_size=100)
    nn_dist, nn_indices = kd_tree.query(
        np.array(doc[vector_field_name]).reshape(1, -1),
        k=min(num_recommendations + 1, vectors.shape[0])  # Add 1 because we filter out the query vector
    )

    # Filtering out the query document itself
    nn_docs = data[nn_indices.flatten()]
    nn_dist = nn_dist.flatten()
    non_query_indices = [i for i, v in enumerate(nn_docs) if v['text_original'] != doc['text_original']]

    return nn_docs[non_query_indices].tolist(), nn_dist[non_query_indices].tolist()


def _get_all_concepts_in_candidates(factor_docs):
    concepts = list(map(lambda x: x['candidates'], factor_docs))
    concepts = [item for sublist in concepts for item in sublist]
    concepts = list(set(list(map(lambda x: x['name'], concepts))))
    return concepts


def _map_concept_candidates_to_distribution(concepts):
    def _map(factor_docs):
        concept_dist = np.full(len(concepts), 0.0001)
        for candidate in factor_docs['candidates']:
            candidate_idx = concepts.index(candidate['name'])
            concept_dist[candidate_idx] = candidate['score']
        return concept_dist
    return _map


def kl_divergence(doc, data, num_recommendations):
    concepts = _get_all_concepts_in_candidates(data)
    concept_candidate_distributions = np.array(list(map(_map_concept_candidates_to_distribution(concepts), data)))

    # Get kl divergence scores
    doc_concept_candidate_dist = np.array(_map_concept_candidates_to_distribution(concepts)(doc))

    kl_divergence_scores = np.array([entropy(doc_concept_candidate_dist, f_dist) for f_dist in concept_candidate_distributions])
    if (kl_divergence_scores.shape[0] > 0 and np.max(kl_divergence_scores) > 0):
        kl_divergence_scores /= np.max(kl_divergence_scores)

    sorted_indices = np.argsort(kl_divergence_scores)
    factors_sorted = np.array(data)[sorted_indices]
    kl_divergence_scores_sorted = kl_divergence_scores[sorted_indices]

    # Filtering out the query document itself
    non_query_indices = [i for i, v in enumerate(factors_sorted) if v['text_original'] != doc['text_original']]
    factor_kl_nn = factors_sorted[non_query_indices][:num_recommendations].flatten().tolist()
    factor_kl_scores = kl_divergence_scores_sorted[non_query_indices][:num_recommendations].tolist()

    return factor_kl_nn, factor_kl_scores
