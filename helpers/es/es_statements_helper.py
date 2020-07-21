import os
from services import es_service


_statement_index_mapping = {
    'properties': {
        'statement_text_original': {'type': 'keyword'},
        'statement_text_cleaned': {'type': 'keyword'},
        'cluster_id': {'type': 'integer'}
    }
}


def get_statement_vector_field_name(dim):
    return f'statement_vector_{dim}_d'


def get_statement_index_mapping():
    return _statement_index_mapping


def map_statement_vector(statements, dim):
    statement_vector_field_name = get_statement_vector_field_name(dim)

    def _map(statement):
        statement['statement_vector'] = statement[statement_vector_field_name]
        return statement

    return list(map(_map, statements))


def get_all_statements(statement_index_name, source_fields):

    def _map_statement_source(statement_doc):
        statement = statement_doc['_source']
        statement['id'] = statement_doc['_id']
        return statement

    es_client = es_service.get_client()
    data = es_client.search(
        index=statement_index_name,
        size=10000,
        scroll='2m',
        _source_includes=source_fields,
        body={
            'query': {
                'match_all': {}
            }
        }
    )

    sid = data['_scroll_id']
    scroll_size = len(data['hits']['hits'])

    statements = []
    while scroll_size > 0:
        statements = statements + data['hits']['hits']

        data = es_client.scroll(scroll_id=sid, scroll='2m')
        sid = data['_scroll_id']
        scroll_size = len(data['hits']['hits'])

    es_client.clear_scroll(scroll_id=sid)

    mapped_statements = list(map(_map_statement_source, statements))
    return mapped_statements


def get_cluster_id(statement_index_name, statement_text_original):
    es_client = es_service.get_client()
    data = es_client.search(
        index=statement_index_name,
        size=1,
        scroll='5m',
        _source_includes=['cluster_id'],
        body={
            'query': {
                'bool': {
                    'filter': [
                        {'term': {'statement_text_original': statement_text_original}}
                    ]
                }
            }
        }
    )

    docs = data['hits']['hits']
    if len(docs) < 1:
        raise AssertionError  # TODO: Fix

    return docs[0]['_source']['cluster_id']


def get_statements_in_same_cluster(statement_index_name, cluster_id, clustering_dim):
    statement_vector_field_name = get_statement_vector_field_name(clustering_dim)

    def _map_source(statement_doc):
        statement = statement_doc['_source']
        statement['statement_vector'] = statement[statement_vector_field_name]
        statement.pop(statement_vector_field_name, None)
        return statement

    es_client = es_service.get_client()
    data = es_client.search(
        index=statement_index_name,
        size=10000,
        scroll='5m',
        _source_includes=['statement_text_original', 'statement_text_cleaned', statement_vector_field_name],
        body={
            'query': {
                'bool': {
                    'filter': [
                        {'term': {'cluster_id': cluster_id}}
                    ]
                }
            }
        }
    )

    sid = data['_scroll_id']
    scroll_size = len(data['hits']['hits'])

    results = []
    while scroll_size > 0:
        results = results + list(map(_map_source, data['hits']['hits']))

        data = es_client.scroll(scroll_id=sid, scroll='2m')
        sid = data['_scroll_id']
        scroll_size = len(data['hits']['hits'])

    es_client.clear_scroll(scroll_id=sid)
    print(f'Finished fetching all statements for cluster {cluster_id}')
    return results


def get_statement(statement_index_name, statement_text_original):
    es_client = es_service.get_client()
    data = es_client.search(
        index=statement_index_name,
        size=1,
        scroll='5m',
        body={
            'query': {
                'bool': {
                    'filter': [
                        {'term': {'statement_text_original': statement_text_original}}
                    ]
                }
            }
        }
    )

    docs = data['hits']['hits']
    if len(docs) < 1:
        raise AssertionError  # TODO: Fix

    return docs[0]['_source']
