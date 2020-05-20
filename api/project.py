from services import es_service
from flask import Blueprint, request, jsonify
from es_helpers import es_factors_helper
from werkzeug.exceptions import BadRequest
project_api = Blueprint('project_api', __name__)


@project_api.route('/create', methods=['POST'])
def create_project():
    body = request.get_json()
    project_id = body['project_id']
    source_knowledge_base_id = body['source_knowledge_base_id']

    project_index_name = es_service.get_curation_project_index_name(project_id)
    kb_index_name = es_service.get_curation_kb_index_name(source_knowledge_base_id)
    es_client = es_service.get_client()

    if es_client.indices.exists(index=project_index_name) is True:
        raise BadRequest(f"Index, {project_index_name}, already exists.")

    if es_client.indices.exists(index=kb_index_name) is False:
        raise BadRequest(f"Knowledge Base index, {kb_index_name}, does not exist")

    es_client.indices.create(
        index=project_index_name,
        body={
            'mappings': es_factors_helper.get_project_index_mapping()
        }
    )
    task = es_client.reindex(
        wait_for_completion=False,
        body={
            'source': {
                'index': kb_index_name
            },
            'dest': {
                'index': project_index_name
            }
        }
    )
    return jsonify(task)


@project_api.route('/create/status', methods=['GET'])
def project_creation_status():
    task_id = request.args.get('task_id')

    task_client = es_service.get_tasks_client()
    task_info = task_client.get(task_id=task_id)

    # FIXME: Return only relevant fields here
    return jsonify(task_info)


@project_api.route('/delete', methods=['POST'])
def delete_project():
    body = request.get_json()
    project_id = body['project_id']
    project_index_name = es_service.get_curation_project_index_name(project_id)

    es_client = es_service.get_client()
    if es_client.indices.exists(index=project_index_name) is False:
        raise BadRequest(f"Index, {project_index_name}, does not exist.")
    es_client.indices.delete(index=project_index_name)

    return jsonify({})
