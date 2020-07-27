import os
from services import es_service
from helpers.es import es_recommendations_helper


def setup_recommendation_index():
    _delete_recommendation_index()
    _create_recommendation_index()


def _delete_recommendation_index():
    es_client = es_service.get_client()
    RECOMMENDATION_INDEX_NAME = es_service.get_recommendation_index_name(os.getenv('KB_INDEX_NAME'))

    if es_client.indices.exists(index=RECOMMENDATION_INDEX_NAME) and os.getenv('DELETE_RECOMMENDATION_INDEX_IF_EXISTS') == 'true':
        print('Deleting recommendation index!')
        es_client.indices.delete(index=RECOMMENDATION_INDEX_NAME)


def _create_recommendation_index():
    es_client = es_service.get_client()
    RECOMMENDATION_INDEX_NAME = es_service.get_recommendation_index_name(os.getenv('KB_INDEX_NAME'))

    if es_client.indices.exists(index=RECOMMENDATION_INDEX_NAME) is False:
        print('Creating recommendation index mapping')
        es_client.indices.create(
            index=RECOMMENDATION_INDEX_NAME,
            body={
                'mappings': es_recommendations_helper.get_recommendation_index_mapping()
            }
        )
