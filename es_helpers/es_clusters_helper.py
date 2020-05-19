from services import es_service, ontology_service
import os


def get_all_factors_for_concept(index_name, concept_name):
    print('Fetching all factors for concept: {}'.format(concept_name))
    es_client = es_service.get_client()

    data = es_client.search(
        index=index_name,
        size=10000,
        scroll='10m',
        body={
            '_source': ['factor_vector_2_d', 'factor_cleaned'],
            'query': {
                'bool': {
                    'filter': {
                        'term': {
                            'concept': concept_name
                        }
                    }
                }
            }
        }
    )

    sid = data['_scroll_id']
    scroll_size = len(data['hits']['hits'])

    results = []
    while scroll_size > 0:
        results = results + data['hits']['hits']

        data = es_client.scroll(scroll_id=sid, scroll='2m')
        sid = data['_scroll_id']
        scroll_size = len(data['hits']['hits'])

    es_client.clear_scroll(scroll_id=sid)
    print('Finished fetching all concepts for {}'.format(concept_name))
    return results


def get_concept_coord(concept_name):
    es_client = es_service.get_client()
    data = es_client.search(
        index=os.getenv('CONCEPTS_INDEX_NAME'),
        _source_includes=['concept_vector_2_d'],
        size=1,
        body={
            'query': {
                'bool': {
                    'filter': {
                        'term': {
                            'concept': concept_name
                        }
                    }
                }
            }
        }
    )

    if len(data['hits']['hits']) == 0:
        raise AssertionError  # TODO: Fix

    return data['hits']['hits'][0]['_source']['concept_vector_2_d']


def get_cluster_map(index_name, concept, statement_ids):
    es_client = es_service.get_client()
    data = es_client.search(
        index=index_name,
        size=10000,
        scroll='5m',
        _source_includes=['statement_id', 'type', 'cluster_id', 'factor_vector_2_d'],
        body={
            'query': {
                'bool': {
                    'filter': {
                        'term': {
                            'concept': concept
                        },
                    },
                    'filter': {
                        'terms': {
                            'statement_id': statement_ids
                        }
                    }
                }
            }
        }
    )

    sid = data['_scroll_id']
    scroll_size = len(data['hits']['hits'])

    results = []
    while scroll_size > 0:
        results = results + list(map(lambda x: x['_source'], data['hits']['hits']))

        data = es_client.scroll(scroll_id=sid, scroll='2m')
        sid = data['_scroll_id']
        scroll_size = len(data['hits']['hits'])

    es_client.clear_scroll(scroll_id=sid)
    print('Finished fetching all concepts for {}'.format(concept))
    return results
