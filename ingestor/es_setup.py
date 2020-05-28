import os
from services import es_service
from es_helpers import es_factors_helper, es_concepts_helper, es_recommendation_decisions_helper


def setup_outgoing_kb_index():
    _delete_outgoing_kb_index()
    _create_outgoing_kb_index()


def setup_concept_index():
    _delete_concept_index()
    _create_concept_index()


def setup_recommendation_decisions_index():
    es_client = es_service.get_client()
    RECOMMENDATION_DECISIONS_INDEX_NAME = os.getenv('RECOMMENDATION_DECISIONS_INDEX_NAME')

    if es_client.indices.exists(index=RECOMMENDATION_DECISIONS_INDEX_NAME) is False:
        print('Setting recommendation decisions index mapping')
        es_client.indices.create(
            index=RECOMMENDATION_DECISIONS_INDEX_NAME,
            body={
                'mappings': es_recommendation_decisions_helper.get_recommendation_decisions_index_mapping()
            }
        )


def _delete_outgoing_kb_index():
    es_client = es_service.get_client()
    OUTGOING_KB_INDEX_NAME = es_service.get_curation_kb_index_name(os.getenv('INCOMING_KB_INDEX_NAME'))

    if es_client.indices.exists(index=OUTGOING_KB_INDEX_NAME) and os.getenv('DELETE_OUTGOING_KB_INDEX_IF_EXISTS') == 'true':
        print('Deleting outgoing kb index!')
        es_client.indices.delete(index=OUTGOING_KB_INDEX_NAME)


def _create_outgoing_kb_index():
    es_client = es_service.get_client()
    OUTGOING_KB_INDEX_NAME = es_service.get_curation_kb_index_name(os.getenv('INCOMING_KB_INDEX_NAME'))

    if es_client.indices.exists(index=OUTGOING_KB_INDEX_NAME) is False:
        print('Setting outgoing kb index mapping')
        es_client.indices.create(
            index=OUTGOING_KB_INDEX_NAME,
            body={
                'mappings': es_factors_helper.get_kb_index_mapping()
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
                'mappings': es_concepts_helper.get_concept_index_mapping()
            }
        )
