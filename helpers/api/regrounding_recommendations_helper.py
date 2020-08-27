import statistics
from helpers.api import recommendations_helper
from helpers.es import es_kb_helper


def compute_kl_divergence_nn(factor_reco_doc, statement_ids, num_recommendations, project_index_id, factor_reco_index_id):
    def _map_kl_nn_results(factor, score):
        return {
            'factor': factor['text_original'],
            'score': score
        }

    factors_in_cluster = recommendations_helper.get_recommendations_in_cluster(factor_reco_doc['cluster_id'], factor_reco_index_id)
    kl_nn_factors, kl_nn_scores = recommendations_helper.compute_kl_divergence(
        factor_reco_doc, factors_in_cluster, statement_ids, num_recommendations, project_index_id)
    kl_nn = list(map(_map_kl_nn_results, kl_nn_factors, kl_nn_scores))
    return kl_nn


def compute_knn(factor_reco_doc, statement_ids, num_recommendations, project_index_id, factor_reco_index_id):
    def _map_knn_results(factor, score):
        return {
            'factor': factor['_source']['text_original'],
            'score': score
        }

    fields_to_include = ['text_original']
    query_filter = _build_query_filter(factor_reco_doc, statement_ids, project_index_id)
    knn_factors, knn_scores = recommendations_helper.compute_knn(factor_reco_doc, fields_to_include, query_filter, num_recommendations, factor_reco_index_id)
    knn = list(map(_map_knn_results, knn_factors, knn_scores))
    return knn


def _build_query_filter(factor_reco_doc, statement_ids, project_index_id):
    factors = es_kb_helper.get_factors_for_statement_ids(statement_ids, project_index_id)
    query = {
        'bool': {
            'filter': [
                {'term': {'cluster_id': factor_reco_doc['cluster_id']}},
                {'terms': {'text_original': factors}}
            ]
        }
    }
    return query


def combine_results(knn_results, kl_nn_results):
    combined_results = []
    factor_scores_mapping = _create_factor_scores_mapping(knn_results, kl_nn_results)

    for factor, scores in factor_scores_mapping.items():
        combined_results.append({
            'factor': factor,
            # This is to make sure that scores found using both heuristics have lower distance and so are higher rated
            'score': statistics.mean(scores) if len(scores) > 1 else scores[0] + 1
        })

    return combined_results


def _create_factor_scores_mapping(knn_results, kl_nn_results):
    factor_scores_mapping = {}

    def _add_to_factor_scores_mapping(result):
        factor = result['factor']
        score = result['score']
        if factor in factor_scores_mapping:
            factor_scores_mapping[factor].append(score)
        else:
            factor_scores_mapping[factor] = [score]

    for result in knn_results:
        _add_to_factor_scores_mapping(result)

    for result in kl_nn_results:
        _add_to_factor_scores_mapping(result)

    return factor_scores_mapping
