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


def get_project_index_mapping():
    return _factor_index_mapping


def get_all_factor_vectors(factor_index_name, dim):
    print('Fetching all factor vectors.')
    factor_vector_field_name = get_factor_vector_field_name(dim)
    es_factors = get_all_factors(
        factor_index_name=factor_index_name,
        source_fields=[factor_vector_field_name]
    )
    mapped_factors = _map_es_factors(es_factors, factor_vector_field_name)
    print('Finished fetching all factor vectors.')
    return mapped_factors


def _map_es_factors(es_factors, factor_vector_field_name):
    def _map(es_factor_doc):
        return {
            'factor_vector': es_factor_doc['_source'][factor_vector_field_name],
            'id': es_factor_doc['_id']
        }
    return list(map(_map, es_factors))


def get_all_factors(factor_index_name, source_fields):
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

    return factors


def get_factor(index_name, statement_id, factor_type):
    es_client = es_service.get_client()
    data = es_client.search(
        index=index_name,
        body={
            'query': {
                'bool': {
                    'filter': [
                        {'term': {'statement_id': statement_id}},
                        {'term': {'type': factor_type}}
                    ]
                }
            }
        }
    )
    return data['hits']['hits'][0]['_source']
