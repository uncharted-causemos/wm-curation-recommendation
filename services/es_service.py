from elasticsearch import Elasticsearch
from elasticsearch.client import TasksClient
import os

client = None
tasks_client = None


def _init_client():
    global _client
    _client = Elasticsearch(
        os.getenv("ES_HOST"),
        http_auth=("", ""),  # TODO LATER: add authentication
        scheme="http",
        port=os.getenv("ES_PORT")
    )


def _init_tasks_client():
    global _tasks_client
    _tasks_client = TasksClient(client)


def get_client():
    # TODO: check client is still active
    return _client


def tasks_client():
    # TODO: check client is still active
    return _tasks_client


_init_client()
_init_tasks_client()
