from flask import Blueprint, request, jsonify
from helpers.api import recommendations_helper

regrounding_recommendations_api = Blueprint('regrounding_recommendations_api', __name__)


@regrounding_recommendations_api.route('/', methods=['POST'])
def get_recommendations():
    body = request.get_json()
    project_index_id = body['project_id']
    kb_index_id = body['kb_id']
    factor_text_original = body['factor']
    num_recommendations = body['num_recommendations']

    factor_doc = recommendations_helper.get_factor(factor_text_original, kb_index_id)

    if factor_doc['cluster_id'] == -1:
        response = {
            'factor_recommendations': []
        }
        return jsonify(response)

    factors_in_cluster = recommendations_helper.get_factors_in_cluster(factor_doc['cluster_id'], kb_index_id)
    knn = recommendations_helper.compute_knn(factor_doc, factors_in_cluster, num_nn=num_recommendations)
    kl_nn = recommendations_helper.compute_kl_divergence(factor_doc, factors_in_cluster, project_index_id, num_nn=num_recommendations)

    recommended_factors = knn + kl_nn
    response = {
        'factor_recommendations': recommended_factors
    }
    return jsonify(response)
