import os
from services import es_service


_factor_index_mapping = {
    'properties': {
        'factor_text_original': {'type': 'keyword'},
        'factor_text_cleaned': {'type': 'keyword'},
        'cluster_id': {'type': 'integer'}
    }
}


def get_factor_vector_field_name(dim):
    return f'factor_vector_{dim}_d'


def get_kb_index_mapping():
    return _factor_index_mapping


def map_factor_vector(factors, dim):
    factor_vector_field_name = get_factor_vector_field_name(dim)

    def _map(factor):
        factor['factor_vector'] = factor[factor_vector_field_name]
        return factor

    return list(map(_map, factors))


def get_all_factors(factor_index_name, source_fields):

    def _map_factor_source(factor_doc):
        factor = factor_doc['_source']
        factor['id'] = factor_doc['_id']
        return factor

    es_client = es_service.get_client()
    data = es_client.search(
        index=factor_index_name,
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

    factors = []
    while scroll_size > 0:
        factors = factors + data['hits']['hits']

        data = es_client.scroll(scroll_id=sid, scroll='2m')
        sid = data['_scroll_id']
        scroll_size = len(data['hits']['hits'])

    es_client.clear_scroll(scroll_id=sid)

    mapped_factors = list(map(_map_factor_source, factors))
    return mapped_factors


def get_cluster_id(factor_index_name, factor_text_original):
    es_client = es_service.get_client()
    data = es_client.search(
        index=factor_index_name,
        size=1,
        scroll='5m',
        _source_includes=['cluster_id'],
        body={
            'query': {
                'bool': {
                    'filter': [
                        {'term': {'factor_text_original': factor_text_original}}
                    ]
                }
            }
        }
    )

    docs = data['hits']['hits']
    if len(docs) < 1:
        raise AssertionError  # TODO: Fix

    return docs[0]['_source']['cluster_id']


def get_factors_in_same_cluster(factor_index_name, cluster_id, clustering_dim):
    factor_vector_field_name = get_factor_vector_field_name(clustering_dim)

    def _map_source(factor_doc):
        factor = factor_doc['_source']
        factor['factor_vector'] = factor[factor_vector_field_name]
        factor.pop(factor_vector_field_name, None)
        return factor

    es_client = es_service.get_client()
    data = es_client.search(
        index=factor_index_name,
        size=10000,
        scroll='5m',
        _source_includes=['factor_text_original', 'factor_text_cleaned', factor_vector_field_name],
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
    print(f'Finished fetching all factors for cluster {cluster_id}')
    return results


def get_factor(factor_index_name, factor_text_original):
    es_client = es_service.get_client()
    data = es_client.search(
        index=factor_index_name,
        size=1,
        scroll='5m',
        body={
            'query': {
                'bool': {
                    'filter': [
                        {'term': {'factor_text_original': factor_text_original}}
                    ]
                }
            }
        }
    )

    docs = data['hits']['hits']
    if len(docs) < 1:
        raise AssertionError  # TODO: Fix

    return docs[0]['_source']
