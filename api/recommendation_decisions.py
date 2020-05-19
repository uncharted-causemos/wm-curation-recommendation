import os
from flask import Blueprint, request, jsonify
from es_helpers import es_factors_helper, es_recommendation_decisions_helper
from services import es_service

recommendation_decisions_api = Blueprint('recommendation_decisions_api', __name__)


@recommendation_decisions_api.route('/regrounding', methods=['POST'])
def regrounding_recommendation_decisions():
    body = request.get_json()
    statement_id = body['statement_id']
    factor_type = body['type']
    new_concept = body['new_concept']
    project_id = body['project_id']
    recommendation_decisions = body['recommendation_decisions']

    _process_regrounding_recommendation_decisions(es_service.get_curation_kb_index_name(os.getenv('INCOMING_KB_INDEX_NAME')), project_id, new_concept,
                                                  statement_id, factor_type, recommendation_decisions)

    # TODO: If the decision to recompute cluster_ids immediately is made, a separate threaded call to cluster_service should be made here

    return jsonify({})


@recommendation_decisions_api.route('/polarity/', methods=['POST'])
def polarity_recommendation_decisions():
    return 'Not implemented yet.'


def _process_regrounding_recommendation_decisions(kb_id, project_id, new_concept, statement_id, factor_type, recommendation_decisions):
    def _map_regrounding_rd(rd):
        return {
            'curation_type': 'regrounding',
            'project_id': project_id,
            'kb_id': kb_id,  # FIXME: I should actually be extracted from the project index
            'curation': {
                'statement_id': statement_id,
                'type': factor_type,
                'old_concept': old_concept,
                'new_concept': new_concept,
            },
            'recommendations': {
                'statement_id': rd['statement_id'],
                'type': rd['type'],
                'accepted': rd['accepted']
            }
        }

    project_index_name = es_service.get_curation_project_index_name(project_id)

    factor = es_factors_helper.get_factor(project_index_name, statement_id, factor_type)
    old_concept = factor['concept']  # The assumption in setting old_concept here is that regrounding recommendations were restricted to a particular concept

    recommendation_decision_docs = list(map(_map_regrounding_rd, recommendation_decisions))
    es_recommendation_decisions_helper.insert_recommendation_decisions(recommendation_decision_docs)
