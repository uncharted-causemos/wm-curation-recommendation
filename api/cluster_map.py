from flask import Blueprint, request, jsonify
from es_helpers import es_clusters_helper
from services import es_service

cluster_map_api = Blueprint('cluster_map_api', __name__)


@cluster_map_api.route('/', methods=['POST'])
def get_cluster_map():
    body = request.get_json()
    concept = body['concept']
    statement_ids = body['statement_subspace']
    project_id = body['project_id']

    project_index_name = es_service.get_curation_project_index_name(project_id)

    factor_cluster_map = es_clusters_helper.get_cluster_map(project_index_name, concept, statement_ids)
    concept_coord = es_clusters_helper.get_concept_coord(concept)

    response = {
        'concept': _format_concept_cluster_point(concept_coord),
        'factors': list(map(_format_factor_cluster_point, factor_cluster_map))
    }

    return jsonify(response)


def _format_factor_cluster_point(factor_cluster_point):
    return {
        'statement_id': factor_cluster_point['statement_id'],
        'type': factor_cluster_point['type'],
        'cluster_id': factor_cluster_point['cluster_id'],
        'coords': {
            'x': float(factor_cluster_point['factor_vector_2_d'][0]),
            'y': float(factor_cluster_point['factor_vector_2_d'][1])
        }
    }


def _format_concept_cluster_point(concept_cluster_point):
    return {
        'coords': {
            'x': float(concept_cluster_point[0]),
            'y': float(concept_cluster_point[1])
        }
    }
