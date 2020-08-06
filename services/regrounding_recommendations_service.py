from functools import reduce
from helpers.api import recommendations_helper
from services import es_service


def compute_kl_divergence_nn(factor_reco_doc, project_index_id, factor_reco_index_id):
    def _map_kl_nn_results(f):
        return {
            'factor': f['text_original']
        }

    factors_in_cluster = recommendations_helper.get_recommendations_in_cluster(factor_reco_doc['cluster_id'], factor_reco_index_id)
    kl_nn = recommendations_helper.compute_kl_divergence(factor_reco_doc, factors_in_cluster, project_index_id)
    kl_nn = list(map(_map_kl_nn_results, kl_nn.flatten().tolist()))
    return kl_nn


def compute_knn(factor_reco_doc, statement_ids, project_index_id, factor_reco_index_id):
    def _map_knn_results(f):
        return {
            'factor': f['_source']['text_original']
        }

    fields_to_include = ['text_original']
    query_filter = _build_query_filter(factor_reco_doc, statement_ids, project_index_id)
    knn = recommendations_helper.compute_knn(factor_reco_doc, fields_to_include, query_filter, factor_reco_index_id)
    knn = list(map(_map_knn_results, knn))
    return knn


def _build_query_filter(factor_reco_doc, statement_ids, project_index_id):
    factors = _get_factors_for_statement_ids(statement_ids, project_index_id)
    query = {
        'bool': {
            'filter': [
                {'term': {'cluster_id': factor_reco_doc['cluster_id']}},
                {'terms': {'text_original': factors}}
            ]
        }
    }
    return query


def _get_factors_for_statement_ids(statement_ids, project_index_id):
    def _map_source(statement):
        return [
            statement['_source']['subj']['factor'],
            statement['_source']['obj']['factor']
        ]

    def _reduce_source(factors, subj_obj_pairs):
        return factors + subj_obj_pairs

    es_client = es_service.get_client()
    data = es_client.search(
        index=project_index_id,
        size=10000,  # Max number of recommendations allowed
        _source_includes=['subj.factor', 'obj.factor'],
        body={
            'query': {
                'bool': {
                    'filter': {
                        'terms': {'id': statement_ids}
                    }
                }
            }
        }
    )

    return list(reduce(_reduce_source, map(_map_source, data['hits']['hits'])))
