from elastic.elastic_indices import get_statement_recommendation_index_id

from services.recommendation import get_recommendation_from_es
from services.utils import knn

try:
    from flask import current_app as app
except ImportError as e:
    print(e)


def get_candidate(subj, obj, index_name, es=None):
    statement = subj + ' ' + obj
    statement_index_name = get_statement_recommendation_index_id(index_name)

    # Attempt to get the recommendation from es
    return get_recommendation_from_es(statement_index_name, statement, es=es)


# Helper for the compute_knn function
def _build_query_filter(statement, statement_ids, polarity, project_index_id, es=None):
    # Helper for getting the subj obj pairs
    def _map_source(statement):
        source = statement['_source']
        return {
            'subj_factor': source['subj']['factor'],
            'obj_factor': source['obj']['factor']
        }

    # Get the subj/obj pairs from es
    body = {
        'query': {
            'bool': {
                'filter': [
                    {'terms': {'id': statement_ids}},
                    {'term': {'wm.statement_polarity': polarity}}
                ]
            }
        }
    }
    response = (es or app.config['ES']).search(
        project_index_id, body, size=10000, _source_includes=['subj.factor', 'obj.factor'])
    pairs = list(map(_map_source, response['hits']['hits']))

    # Helper for builign the should query
    def _map_should_query(pair):
        return {
            'bool': {
                'must': [
                    {'term': {'subj_factor': pair['subj_factor']}},
                    {'term': {'obj_factor': pair['obj_factor']}}
                ]
            }
        }

    # Return the filter query
    return {
        'bool': {
            'filter': [
                {'term': {'cluster_id': statement['cluster_id']}},
            ],
            'should': list(map(_map_should_query, pairs)),
            'minimum_should_match': 1
        }
    }


# compute_knn computes the knn of statements
def compute_knn(statement, statement_ids, polarity, num_recommendations, project_index, knowledge_base_index, es=None):
    statement_index_name = get_statement_recommendation_index_id(
        knowledge_base_index)

    def _map_knn_results(statement, score):
        return {
            'subj_factor': statement['subj_factor'],
            'obj_factor': statement['obj_factor'],
            'score': score
        }

    body = {
        'query': _build_query_filter(statement, statement_ids, polarity, project_index)
    }
    response = (es or app.config['ES']).search(
        statement_index_name, body, size=num_recommendations)

    # Compute knn using the generalized knn method
    knn_factors, knn_scores = knn(
        statement,
        list(map(lambda x: x['_source'], response['hits']['hits'])),
        num_recommendations
    )
    return list(map(_map_knn_results, knn_factors, knn_scores))
