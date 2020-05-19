import os
from flask import Blueprint, request, jsonify
from es_helpers import es_factors_helper, es_recommendations_helper
from services import es_service

recommendations_api = Blueprint('recommendations_api', __name__)


@recommendations_api.route('/regrounding', methods=['POST'])
def regrounding_recommendations():
    body = request.get_json()
    statement_id = body['statement_id']
    factor_type = body['type']
    new_concept = body['new_concept']
    statement_subspace = body['statement_subspace']
    project_id = body['project_id']

    project_index_name = es_service.get_curation_project_index_name(project_id)

    results = []
    results = results + _get_factors_from_same_cluster(project_index_name, statement_id, factor_type)
    results = results + _get_factors_from_same_docs(project_index_name, statement_id, factor_type)
    results = results + _get_factors_with_similar_candidates()

    results = list(map(lambda x: {'statement_id': x['statement_id'], 'type': x['type']}, results))

    return jsonify(results)


@recommendations_api.route('/polarity', methods=['GET'])
def polarity_recommendations():
    return 'Not implemented yet.'


def _get_factors_with_similar_candidates():
    # TODO: Recommend factors based on concept scores
    return []


def _get_factors_from_same_cluster(project_index_name, statement_id, factor_type):
    factor = es_factors_helper.get_factor(project_index_name, statement_id, factor_type)
    factors_with_same_cluster_id = es_recommendations_helper.get_all_factors_with_cluster_id(project_index_name, factor['concept'], factor['cluster_id'])
    return factors_with_same_cluster_id


def _get_factors_from_same_docs(project_index_name, statement_id, factor_type):
    # FIXME: I'm getting num evidence from the knowledge base. This might be an issue if say the knowledge base that the project was based on changes
    kb_index_name = os.getenv('INCOMING_KB_INDEX_NAME')
    statement_num_evidences = es_recommendations_helper.get_number_evidences(kb_index_name, statement_id, factor_type)

    # We're only focused on suggesting factors that came from the same doc, since aobut 80% of the factors are based on the
    if statement_num_evidences != 1:
        return []

    statement_doc_id = es_recommendations_helper.get_statement_doc_id(kb_index_name, statement_id, factor_type)
    shared_doc_id_statement_ids = es_recommendations_helper.get_statement_ids_with_doc_ids(kb_index_name, statement_doc_id)
    factors_with_same_doc_id = es_recommendations_helper.get_all_factors_with_statement_ids(project_index_name, shared_doc_id_statement_ids)
    return factors_with_same_doc_id
