import os
from services import es_service, ontology_service
from helpers.es import es_recommendations_helper, es_kb_helper
from scipy.stats import entropy
import numpy as np


def get_reco_doc(text_original, index_id):
    reco_doc = es_recommendations_helper.get_recommendation(index_id, text_original)
    clustering_vector_field_name = es_recommendations_helper.get_dim_vector_field_name(os.getenv('CLUSTERING_DIM'))
    reco_doc['vector'] = reco_doc[clustering_vector_field_name]
    return reco_doc


def get_recommendations_in_cluster(cluster_id, index_id):
    clustering_dim = os.getenv('CLUSTERING_DIM')
    recommendations_in_cluster = es_recommendations_helper.get_recommendations_in_same_cluster(index_id, cluster_id, clustering_dim)
    return recommendations_in_cluster


def compute_knn(query_doc, fields_to_include, query_filter, num_recommendations, index_id):
    clustering_dim = os.getenv("CLUSTERING_DIM")
    vector_field_name = es_recommendations_helper.get_dim_vector_field_name(clustering_dim)
    es_client = es_service.get_client()
    data = es_client.search(
        index=index_id,
        # TODO: Currently this is set to 1K because CauseMos will filter for visible graph (and potentially polarity). Also max number of docs in cluster is roughly 500
        size=num_recommendations,  # Max number of recommendations
        _source_includes=fields_to_include,
        body={
            'query': {
                'script_score': {
                    'query': query_filter,
                    'script': {
                        'source': f"cosineSimilarity(params.query_vector, '{vector_field_name}')",
                        'params': {'query_vector': query_doc[vector_field_name]}
                    }
                }
            }
        }
    )

    print('Finished fetching all recommendations for statement')
    return data['hits']['hits']


def compute_kl_divergence(query_doc, all_recos, num_recommendations, project_index_id):
    text_originals = list(map(lambda x: x['text_original'], all_recos))

    factors_concept_candidates = es_kb_helper.get_concept_candidates_for_all_factors(text_originals, project_index_id)
    factor_concept_candidate_distributions = np.array(list(map(_map_concept_candidates_to_distribution, factors_concept_candidates)))

    factor_doc_concept_candidate = es_kb_helper.get_concept_candidates_for_factor(query_doc['text_original'], project_index_id)
    factor_doc_concept_candidate_dist = np.array(_map_concept_candidates_to_distribution(factor_doc_concept_candidate))

    kl_divergence_scores = np.array([entropy(factor_doc_concept_candidate_dist, f_dist) for f_dist in factor_concept_candidate_distributions])
    sorted_indices = np.argsort(kl_divergence_scores)
    factors_sorted = np.array(factors_concept_candidates)[sorted_indices]
    return factors_sorted[:num_recommendations]


def _map_concept_candidates_to_distribution(factor_concept_candidate):
    concept_names = ontology_service.get_concept_names()
    concept_dist = np.full(len(concept_names), 0.0001)
    for candidate in factor_concept_candidate['candidates']:
        candidate_idx = concept_names.index(candidate['name'])
        concept_dist[candidate_idx] = candidate['score']
    return concept_dist
