from flask import Blueprint, request, jsonify
from helpers.api import recommendations_helper
from helpers.es import es_recommendations_helper

regrounding_recommendations_api = Blueprint('regrounding_recommendations_api', __name__)


@regrounding_recommendations_api.route('/', methods=['POST'])
def get_recommendations():
    body = request.get_json()
    project_index_id = body['project_id']
    kb_index_id = body['kb_id']
    factor_text_original = body['factor']
    factor_reco_index_id = es_recommendations_helper.get_factor_recommendation_index_id(kb_index_id)

    factor_doc = recommendations_helper.get_reco_doc(factor_text_original, kb_index_id)

    if factor_doc['cluster_id'] == -1:
        _build_response([])

    knn = _compute_knn(factor_doc, factor_reco_index_id)
    kl_nn = _compute_kl_divergence_nn(factor_doc, factor_reco_index_id, project_index_id)

    recommended_factors = knn + kl_nn
    return _build_response(recommended_factors)


def _build_response(recommended_factors):
    response = {
        'recommendations': recommended_factors
    }
    return jsonify(response)


def _map_nn_results(f):
    return f['_source']['text_original']


def _compute_kl_divergence_nn(factor_doc, factor_reco_index_id, project_index_id):
    factors_in_cluster = recommendations_helper.get_recommendations_in_cluster(factor_doc['cluster_id'], factor_reco_index_id)
    kl_nn = recommendations_helper.compute_kl_divergence(factor_doc, factors_in_cluster, project_index_id)
    kl_nn = list(map(_map_nn_results, kl_nn.flatten().tolist()))
    return kl_nn


def _compute_knn(factor_doc, factor_reco_index_id):
    fields_to_include = ['text_original']
    knn = recommendations_helper.compute_knn(factor_doc, fields_to_include, factor_reco_index_id)
    knn = list(map(_map_nn_results, knn))
    return knn
