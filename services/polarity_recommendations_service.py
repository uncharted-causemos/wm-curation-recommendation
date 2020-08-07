from helpers.api import recommendations_helper
from helpers.es import es_recommendations_helper
from services import es_service


def get_reco_doc(subj_factor_text_original, obj_factor_text_original, kb_index_id):
    text_original = subj_factor_text_original + " " + obj_factor_text_original
    statement_reco_index_id = es_recommendations_helper.get_statement_recommendation_index_id(kb_index_id)
    statement_doc = recommendations_helper.get_reco_doc(text_original, statement_reco_index_id)
    return statement_doc


def compute_knn(statement_reco_doc, statement_ids, polarity, num_recommendations, project_index_id, kb_index_id):
    def _map_knn_results(statement_doc):
        return {
            'subj_factor': statement_doc['_source']['subj_factor'],
            'obj_factor': statement_doc['_source']['obj_factor']
        }
    query_filter = _build_query_filter(statement_reco_doc, statement_ids, polarity, project_index_id)
    statement_reco_index_id = es_recommendations_helper.get_statement_recommendation_index_id(kb_index_id)
    fields_to_include = ['subj_factor', 'obj_factor']
    knn = recommendations_helper.compute_knn(statement_reco_doc, fields_to_include, query_filter, num_recommendations, statement_reco_index_id)
    knn = list(map(_map_knn_results, knn))
    return knn


def _build_query_filter(statement_reco_doc, statement_ids, polarity, project_index_id):
    def _map_should_query(sop):
        return {
            'bool': {
                'must': [
                    {'term': {'subj_factor': sop['subj_factor']}},
                    {'term': {'obj_factor': sop['obj_factor']}}
                ]
            }
        }
    subj_obj_pairs = _get_subj_obj_pairs_for_statement_ids(statement_ids, polarity, project_index_id)
    should_query = list(map(_map_should_query, subj_obj_pairs))
    query = {
        'bool': {
            'filter': [
                {'term': {'cluster_id': statement_reco_doc['cluster_id']}},
            ],
            'should': should_query,
            'minimum_should_match': 1
        }
    }
    return query


def _get_subj_obj_pairs_for_statement_ids(statement_ids, polarity, project_index_id):
    def _map_source(statement):
        return {
            'subj_factor': statement['_source']['subj']['factor'],
            'obj_factor': statement['_source']['obj']['factor']
        }

    es_client = es_service.get_client()
    data = es_client.search(
        index=project_index_id,
        size=10000,  # Max number of recommendations allowed
        _source_includes=['subj.factor', 'obj.factor'],
        body={
            'query': {
                'bool': {
                    'filter': [
                        {'terms': {'id': statement_ids}},
                        {'term': {'wm.statement_polarity': polarity}}
                    ]
                }
            }
        }
    )

    return list(map(_map_source, data['hits']['hits']))
