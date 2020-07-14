from elasticsearch import Elasticsearch
from elasticsearch.client import TasksClient
import os

_client = None
_tasks_client = None


def _init_client():
    global _client
    _client = Elasticsearch(
        os.getenv('ES_HOST'),
        http_auth=('', ''),  # TODO LATER: add authentication
        scheme='http',
        port=os.getenv('ES_PORT')
    )


def _init_tasks_client():
    global _tasks_client
    _tasks_client = TasksClient(_client)


def get_client():
    # TODO: check client is still active
    return _client


def get_tasks_client():
    # TODO: check client is still active
    return _tasks_client


def get_curation_project_index_name(project_id):
    return 'curation_recomendations_project_' + project_id


def get_factor_index_name(kb_id):
    return 'factors_' + kb_id


_init_client()
_init_tasks_client()
