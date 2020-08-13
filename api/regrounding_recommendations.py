import math
from flask import Blueprint, request, jsonify
from helpers.api import regrounding_recommendations_helper, recommendations_helper
from helpers.es import es_recommendations_helper
from werkzeug.exceptions import BadRequest


regrounding_recommendations_api = Blueprint('regrounding_recommendations_api', __name__)


@regrounding_recommendations_api.route('/', methods=['POST'])
def get_recommendations():
    body = request.get_json()
    project_index_id = body['project_id']
    kb_index_id = body['kb_id']
    factor_text_original = body['factor']
    num_recommendations = int(body['num_recommendations'])
    statement_ids = body['statement_ids']
    factor_reco_index_id = es_recommendations_helper.get_factor_recommendation_index_id(kb_index_id)

    if num_recommendations > 10000:  # Max num recommendations allowed
        raise BadRequest(description="num_recommendations must not exceed 10,000.")

    factor_doc = recommendations_helper.get_reco_doc(factor_text_original, factor_reco_index_id)

    if factor_doc['cluster_id'] == -1:
        return _build_response([])

    num_knn_recommendations = math.ceil(num_recommendations / 2.0)
    num_kl_nn_recommendations = math.floor(num_recommendations / 2.0)
    knn = regrounding_recommendations_helper.compute_knn(factor_doc, statement_ids, num_knn_recommendations, project_index_id, factor_reco_index_id)
    kl_nn = regrounding_recommendations_helper.compute_kl_divergence_nn(
        factor_doc, statement_ids, num_kl_nn_recommendations, project_index_id, factor_reco_index_id)

    recommended_factors = knn + kl_nn
    return _build_response(recommended_factors)


def _build_response(recommended_factors):
    response = {
        'recommendations': recommended_factors
    }
    return jsonify(response)
