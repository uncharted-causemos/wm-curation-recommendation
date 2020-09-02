import os
from werkzeug.exceptions import BadRequest
from services import es_service
from helpers.es import es_recommendations_helper, es_kb_helper
from scipy.stats import entropy
from sklearn.neighbors import KDTree
import numpy as np


def get_reco_doc(text_original, reco_index_id):
    try:
        reco_doc = es_recommendations_helper.get_recommendation(text_original, reco_index_id)
    except AssertionError as e:
        raise BadRequest(description=e.args[0])

    clustering_vector_field_name = es_recommendations_helper.get_dim_vector_field_name(os.getenv('CLUSTERING_DIM'))
    reco_doc['vector'] = reco_doc[clustering_vector_field_name]
    return reco_doc


def get_recommendations_in_cluster(cluster_id, reco_index_id):
    clustering_dim = os.getenv('CLUSTERING_DIM')
    recommendations_in_cluster = es_recommendations_helper.get_recommendations_in_same_cluster(cluster_id, clustering_dim, reco_index_id)
    return recommendations_in_cluster


def compute_knn(query_doc, fields_to_include, query_filter, num_recommendations, reco_index_id):
    # Commenting out for now but once we have dense vectors back in we can return to this.
    # data = es_client.search(
    #     index=reco_index_id,
    #     size=num_recommendations,  # Max number of recommendations
    #     _source_includes=fields_to_include,
    #     body={
    #         'query': {
    #             'script_score': {
    #                 'query': query_filter,
    #                 'script': {
    #                     'source': f"Math.max(1 - cosineSimilarity(params.query_vector, '{vector_field_name}'), 0)",
    #                     'params': {'query_vector': query_doc[vector_field_name]}
    #                 }
    #             }
    #         }
    #     }
    # )

    clustering_dim = os.getenv("CLUSTERING_DIM")
    vector_field_name = es_recommendations_helper.get_dim_vector_field_name(clustering_dim)
    es_client = es_service.get_client()
    data = es_client.search(
        index=reco_index_id,
        size=10000,
        _source_includes=fields_to_include + [vector_field_name, 'text_original'],
        body={
            'query': query_filter
        }
    )

    docs = np.array(data['hits']['hits'])
    vectors = np.array(list(map(lambda x: x['_source'][vector_field_name], docs)))
    kd_tree = KDTree(vectors, metric='euclidean', leaf_size=100)
    nn_dist, nn_indices = kd_tree.query(
        np.array(query_doc[vector_field_name]).reshape(1, -1),
        k=min(num_recommendations + 1, vectors.shape[0])  # adding 1 to num_recommendations because we won't be returning the query itself
    )

    nn_docs = docs[nn_indices.flatten()]
    nn_dist = nn_dist.flatten()
    non_query_indices = [i for i, v in enumerate(nn_docs) if v['_source']['text_original'] != query_doc['text_original']]

    print('Finished fetching all recommendations for statement')
    return nn_docs[non_query_indices].tolist(), nn_dist[non_query_indices].tolist()  # Filtering out the query document itself


def compute_kl_divergence(query_doc, all_recos, statement_ids, num_recommendations, project_index_id):
    text_originals = list(map(lambda x: x['text_original'], all_recos))

    factors_concept_candidates = es_kb_helper.get_concept_candidates_for_all_factors(text_originals, statement_ids, project_index_id)
    factor_doc_concept_candidate = es_kb_helper.get_concept_candidates_for_factor(query_doc['text_original'], statement_ids, project_index_id)

    concepts = _get_all_concepts_in_candidates(factors_concept_candidates + [factor_doc_concept_candidate])
    factor_concept_candidate_distributions = np.array(list(map(_map_concept_candidates_to_distribution(concepts), factors_concept_candidates)))
    factor_doc_concept_candidate_dist = np.array(_map_concept_candidates_to_distribution(concepts)(factor_doc_concept_candidate))

    kl_divergence_scores = np.array([entropy(factor_doc_concept_candidate_dist, f_dist) for f_dist in factor_concept_candidate_distributions])
    kl_divergence_scores = kl_divergence_scores / \
        np.max(kl_divergence_scores) if (kl_divergence_scores.shape[0] > 0 and np.max(kl_divergence_scores) > 0) else kl_divergence_scores

    sorted_indices = np.argsort(kl_divergence_scores)
    factors_sorted = np.array(factors_concept_candidates)[sorted_indices]
    kl_divergence_scores_sorted = kl_divergence_scores[sorted_indices]

    non_query_indices = [i for i, v in enumerate(factors_sorted) if v['text_original'] != query_doc['text_original']]
    factor_kl_nn = factors_sorted[non_query_indices][:num_recommendations].flatten().tolist()
    factor_kl_scores = kl_divergence_scores_sorted[non_query_indices][:num_recommendations].tolist()

    return factor_kl_nn, factor_kl_scores  # Filtering out the query document itself


def _get_all_concepts_in_candidates(factor_docs):
    concepts = list(map(lambda x: x['candidates'], factor_docs))
    concepts = [item for sublist in concepts for item in sublist]
    concepts = list(set(list(map(lambda x: x['name'], concepts))))
    return concepts


def _map_concept_candidates_to_distribution(concepts):
    def _map(factor_concept_candidate):
        concept_dist = np.full(len(concepts), 0.0001)
        for candidate in factor_concept_candidate['candidates']:
            candidate_idx = concepts.index(candidate['name'])
            concept_dist[candidate_idx] = candidate['score']
        return concept_dist
    return _map
