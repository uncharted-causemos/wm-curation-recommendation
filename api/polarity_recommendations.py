from flask import Blueprint, request, jsonify
from helpers.api import recommendations_helper
from helpers.es import es_recommendations_helper

polarity_recommendations_api = Blueprint('polaritytext_original', __name__)


@polarity_recommendations_api.route('/', methods=['POST'])
def get_recommendations():
    body = request.get_json()
    kb_index_id = body['kb_id']
    subj_factor_text_original = body['subj_factor']
    obj_factor_text_original = body['obj_factor']

    text_original = subj_factor_text_original + " " + obj_factor_text_original
    statement_reco_index_id = es_recommendations_helper.get_statement_recommendation_index_id(kb_index_id)
    statement_doc = recommendations_helper.get_reco_doc(text_original, statement_reco_index_id)

    # TODO:
    if statement_doc['cluster_id'] == -1:
        return _build_response([])

    recommended_statements = _compute_knn(statement_doc, kb_index_id)
    return _build_response(recommended_statements)


def _build_response(recommended_statements):
    response = {
        'recommendations': recommended_statements
    }
    return jsonify(response)


def _compute_knn(statement_doc, kb_index_id):
    def _map_knn_results(statement_doc):
        return {
            'subj_factor': statement_doc['_source']['subj_factor'],
            'obj_factor': statement_doc['_source']['obj_factor']
        }

    statement_index_id = es_recommendations_helper.get_statement_recommendation_index_id(kb_index_id)
    fields_to_include = ['subj_factor', 'obj_factor']
    knn = recommendations_helper.compute_knn(statement_doc, fields_to_include, statement_index_id)
    knn = list(map(_map_knn_results, knn))
    return knn
