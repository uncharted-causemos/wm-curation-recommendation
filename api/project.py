from services import es_service
from flask import Blueprint, request, jsonify

project_api = Blueprint('project_api', __name__)


@project_api.route('/create', methods=['POST'])
def create_project():
    body = request.get_json()
    project_id = body['project_id']
    source_knowledge_base_id = body['source_knowledge_base_id']

    es_client = es_service.get_client()
    # FIXME: Take care of project index already exists error
    task = es_client.reindex(
        wait_for_completion=False,
        body={
            'source': {
                'index': es_service.get_curation_kb_index_name(source_knowledge_base_id)
            },
            'dest': {
                'index': es_service.get_curation_project_index_name(project_id)
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

    # FIXME: Ensure project index exists before deleting (or ignore error in call)
    es_client = es_service.get_client()
    es_client.indices.delete(index=es_service.get_curation_project_index_name(project_id))

    return jsonify({})
