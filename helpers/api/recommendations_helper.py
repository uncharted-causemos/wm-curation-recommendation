import os
from services import es_service
from helpers.es import es_factors_helper


def get_factor(factor_text_original, kb_index_name):
    factor_index_name = es_service.get_factor_index_name(kb_index_name)
    factor_doc = es_factors_helper.get_factor(factor_index_name, factor_text_original)

    clustering_dim = os.getenv('CLUSTERING_DIM')
    factor_vector_field_name = es_factors_helper.get_factor_vector_field_name(clustering_dim)
    factor_doc['factor_vector'] = factor_doc[factor_vector_field_name]

    return factor_doc


def get_factors_in_cluster(cluster_id, kb_index_name):
    clustering_dim = os.getenv('CLUSTERING_DIM')
    factor_index_name = es_service.get_factor_index_name(kb_index_name)
    factors_in_cluster = es_factors_helper.get_factors_in_same_cluster(factor_index_name, cluster_id, clustering_dim)
    return factors_in_cluster


def compute_knn(factor_doc, all_factors, num_nn):
    clustering_dim = os.getenv('CLUSTERING_DIM')
    factor_vector_field_name = es_factors_helper.get_factor_vector_field_name(clustering_dim)
    factor_vector_matrix = utils.build_factor_vector_matrix(all_factors)
    kd_tree = KDTree(factor_vector_matrix, leaf_size=2)
    distances, indices = kd_tree.query(np.array(factor_doc[factor_vector_field_name]).reshape(1, -1), min(num_nn, factor_vector_matrix.shape[0]))
    knn = list(map(lambda d, i: {'score': d, 'factor': all_factors[i]['factor_text_original']}, distances.flatten().tolist(), indices.flatten().tolist()))
    return knn


def compute_kl_divergence(factor_doc, all_factors, kb_index_name, num_nn):
    factor_text_originals = list(map(lambda x: x['factor_text_original'], factors))
    factors_concept_candidates = es_kb_helper.get_concept_candidates(factor_text_originals, kb_index_name)
    factor_concept_candidate_distributions = np.array(list(map(_map_concept_candidates_to_distribution, factors_concept_candidates)))
    factor_doc_concept_candidate = es_kb_helper.get_concept_candidates([factor_doc['factor_text_original']], kb_index_name)[0]
    factor_doc_concept_candidate_dist = np.array(_map_concept_candidates_to_distribution(factor_doc_concept_candidate))
    kl_divergence_scores = np.array([entropy(factor_doc_concept_candidate_dist, f_dist) for f_dist in factor_concept_candidate_distributions])
    sorted_indices = np.argsort(kl_divergence_scores)
    lowest_kl_divergence_factors = np.array(all_factors)[sorted_indices[:num_nn]]
    lowest_kl_divergence_scores = kl_divergence_scores[sorted_indices[:num_nn]]
    kl_nn = list(map(lambda kl_score, factor: {'score': kl_score, 'factor': factor},
                     lowest_kl_divergence_scores.flatten().tolist(),
                     lowest_kl_divergence_factors.flatten().tolist()))
    return kl_nn


def _map_concept_candidates_to_distribution(factor_concept_candidate):
    concept_names = ontology_service.get_concept_names()
    concept_dist = np.zeros((len(concept_names), 1))
    for candidate in factor_concept_candidate['candidates']:
        candidate_idx = concept_names.index(candidate['name'])
        concept_dist[candidate_idx] = candidate['score']
    return concept_dist
