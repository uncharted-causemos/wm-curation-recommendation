import os
from services import es_service


def setup_outgoing_kb_index():
    _delete_outgoing_kb_index()
    _create_outgoing_kb_index()


def setup_concept_index():
    _delete_concept_index()
    _create_concept_index()


def _delete_outgoing_kb_index():
    es_client = es_service.get_client()
    OUTGOING_KB_INDEX_NAME = os.getenv('OUTGOING_KB_INDEX_NAME')

    if es_client.indices.exists(index=OUTGOING_KB_INDEX_NAME) and os.getenv('DELETE_OUTGOING_KB_INDEX_IF_EXISTS') == 'true':
        print('Deleting outgoing kb index!')
        es_client.indices.delete(index=OUTGOING_KB_INDEX_NAME)


def _create_outgoing_kb_index():
    es_client = es_service.get_client()
    OUTGOING_KB_INDEX_NAME = os.getenv('OUTGOING_KB_INDEX_NAME')

    if es_client.indices.exists(index=OUTGOING_KB_INDEX_NAME) is False:
        print('Setting outgoing kb index mapping')
        es_client.indices.create(
            index=OUTGOING_KB_INDEX_NAME,
            body={
                'mappings': {
                    'properties': {
                        'concept': {'type': 'keyword'},
                        'type': {'type': 'keyword'},
                        'factor_cleaned': {'type': 'keyword'},
                        'statement_id': {'type': 'keyword'},
                        'cluster_id': {'type': 'integer'},
                        'polarity': {'type': 'integer'}
                    }
                }
            }
        )


def _delete_concept_index():
    es_client = es_service.get_client()
    CONCEPTS_INDEX_NAME = os.getenv('CONCEPTS_INDEX_NAME')

    if es_client.indices.exists(index=CONCEPTS_INDEX_NAME) and os.getenv('DELETE_CONCEPTS_INDEX_IF_EXISTS') == 'true':
        print('Deleting concepts index!')
        es_client.indices.delete(index=CONCEPTS_INDEX_NAME)


def _create_concept_index():
    es_client = es_service.get_client()
    CONCEPTS_INDEX_NAME = os.getenv('CONCEPTS_INDEX_NAME')

    if es_client.indices.exists(index=CONCEPTS_INDEX_NAME) is False:
        print('Setting concept index mapping')
        es_client.indices.create(
            index=CONCEPTS_INDEX_NAME,
            body={
                'mappings': {
                    'properties': {
                        'concept': {'type': 'keyword'}
                    }
                }
            }
        )
