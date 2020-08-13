from flask import Blueprint, request, jsonify
from helpers.api import polarity_recommendations_helper
from werkzeug.exceptions import BadRequest

polarity_recommendations_api = Blueprint('polaritytext_original', __name__)


@polarity_recommendations_api.route('/', methods=['POST'])
def get_recommendations():
    body = request.get_json()
    project_index_id = body['project_id']
    kb_index_id = body['kb_id']
    subj_factor_text_original = body['subj_factor']
    obj_factor_text_original = body['obj_factor']
    num_recommendations = int(body['num_recommendations'])
    polarity = body['polarity']
    statement_ids = body['statement_ids']

    if num_recommendations > 10000:  # Max num recommendations allowed
        raise BadRequest(description="num_recommendations must not exceed 10,000.")

    statement_doc = polarity_recommendations_helper.get_reco_doc(subj_factor_text_original, obj_factor_text_original, kb_index_id)

    if statement_doc['cluster_id'] == -1:
        return _build_response([])

    recommended_statements = polarity_recommendations_helper.compute_knn(statement_doc,
                                                                         statement_ids,
                                                                         polarity,
                                                                         num_recommendations,
                                                                         project_index_id,
                                                                         kb_index_id)
    return _build_response(recommended_statements)


def _build_response(recommended_statements):
    response = {
        'recommendations': recommended_statements
    }
    return jsonify(response)
