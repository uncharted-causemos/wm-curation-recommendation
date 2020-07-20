import os
from services import es_service
from helpers.es import es_factors_helper


def setup_factor_index():
    _delete_factor_index()
    _create_factor_index()


def _delete_factor_index():
    es_client = es_service.get_client()
    FACTOR_INDEX_NAME = es_service.get_factor_index_name(os.getenv('KB_INDEX_NAME'))

    if es_client.indices.exists(index=FACTOR_INDEX_NAME) and os.getenv('DELETE_FACTOR_INDEX_IF_EXISTS') == 'true':
        print('Deleting factor index!')
        es_client.indices.delete(index=FACTOR_INDEX_NAME)


def _create_factor_index():
    es_client = es_service.get_client()
    FACTOR_INDEX_NAME = es_service.get_factor_index_name(os.getenv('KB_INDEX_NAME'))

    if es_client.indices.exists(index=FACTOR_INDEX_NAME) is False:
        print('Creating factor index mapping')
        es_client.indices.create(
            index=FACTOR_INDEX_NAME,
            body={
                'mappings': es_factors_helper.get_kb_index_mapping()
            }
        )
