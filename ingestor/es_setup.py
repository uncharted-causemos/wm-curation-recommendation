import os
from services import es_service
from helpers.es import es_factors_helper, es_statements_helper


def setup_factor_index():
    _delete_factor_index()
    _create_factor_index()


def setup_statement_index():
    _delete_statement_index()
    _create_statement_index()


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


def _delete_statement_index():
    es_client = es_service.get_client()
    STATEMENT_INDEX_NAME = es_service.get_statement_index_name(os.getenv('KB_INDEX_NAME'))

    if es_client.indices.exists(index=STATEMENT_INDEX_NAME) and os.getenv('DELETE_STATEMENT_INDEX_IF_EXISTS') == 'true':
        print('Deleting statement index!')
        es_client.indices.delete(index=STATEMENT_INDEX_NAME)


def _create_statement_index():
    es_client = es_service.get_client()
    STATEMENT_INDEX_NAME = es_service.get_statement_index_name(os.getenv('KB_INDEX_NAME'))

    if es_client.indices.exists(index=STATEMENT_INDEX_NAME) is False:
        print('Creating statement index mapping')
        es_client.indices.create(
            index=STATEMENT_INDEX_NAME,
            body={
                'mappings': es_statements_helper.get_statement_index_mapping()
            }
        )
