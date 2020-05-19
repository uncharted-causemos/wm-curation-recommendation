from services import es_service

# TODO: Factor out the logic of scrolling through entire sets.


def get_all_factors(index_name, source_fields):
    es_client = es_service.get_client()
    data = es_client.search(
        index=index_name,
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
                    'filter': {
                        'term': {
                            'statement_id': statement_id
                        },
                        'term': {
                            'type': factor_type
                        }
                    }
                }
            }
        }
    )
    return data['hits']['hits'][0]['_source']
