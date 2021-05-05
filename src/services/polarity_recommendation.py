from elastic.elastic_indices import get_statement_recommendation_index_id

from services.recommendation import get_recommendation_from_es
from logic.distance_metrics import DistanceMetrics

try:
    from flask import current_app as app
except ImportError as e:
    print(e)


def get_candidate(subj, obj, index_name, es=None):
    statement = subj + ' ' + obj
    statement_index_name = get_statement_recommendation_index_id(index_name)

    # Attempt to get the recommendation from es
    return get_recommendation_from_es(statement_index_name, statement, es=es)


# compute_knn computes the knn of statements
def compute_knn(statement, num_recommendations, knowledge_base_index, es=None):
    statement_index_name = get_statement_recommendation_index_id(knowledge_base_index)

    def _map_knn_results(statement, score):
        return {
            'subj_factor': statement['subj_factor'],
            'obj_factor': statement['obj_factor'],
            'score': score
        }

    body = {
        'query': {
            'bool': {
                'filter': [
                    {'term': {'cluster_id': statement['cluster_id']}},
                ]
            }
        }
    }
    response = (es or app.config['ES']).search(statement_index_name, body, size=num_recommendations)

    # Compute knn using the generalized knn method
    knn_factors, knn_scores = DistanceMetrics.knn(
        statement,
        list(map(lambda x: x['_source'], response['hits']['hits'])),
        num_recommendations
    )
    return list(map(_map_knn_results, knn_factors, knn_scores))
