from services import es_service
import os

_concept_index_mapping = {
    'properties': {
        'concept': {'type': 'keyword'}
    }
}


def get_concept_index_mapping():
    return _concept_index_mapping


def get_all_concepts():
    es_client = es_service.get_client()
    data = es_client.search(
        index=os.getenv('CONCEPTS_INDEX_NAME'),
        size=10000,
        scroll='2m',
        body={
            'query': {
                'match_all': {}
            }
        }
    )

    sid = data['_scroll_id']
    scroll_size = len(data['hits']['hits'])

    concepts = []
    while scroll_size > 0:
        concepts = concepts + data['hits']['hits']

        data = es_client.scroll(scroll_id=sid, scroll='2m')
        sid = data['_scroll_id']
        scroll_size = len(data['hits']['hits'])

    es_client.clear_scroll(scroll_id=sid)

    return concepts
