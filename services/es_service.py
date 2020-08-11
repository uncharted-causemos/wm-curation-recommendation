from elasticsearch import Elasticsearch
from elasticsearch.client import TasksClient
import os

_client = None
_tasks_client = None


def _init_client():
    global _client
    _client = Elasticsearch(
        os.getenv('ES_HOST'),
        http_auth=('', ''),
        scheme='http',
        port=os.getenv('ES_PORT'),
        timeout=60 * 10,
        retry_on_timeout=True
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


_init_client()
_init_tasks_client()
