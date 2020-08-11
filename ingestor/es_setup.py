from services import es_service
from helpers.es import es_recommendations_helper


def setup_recommendation_indices(factor_reco_index_id,
                                 statement_reco_index_id,
                                 delete_factor_reco_index_if_exists,
                                 delete_statement_reco_index_if_exists):
    _delete_factor_recommendation_index(factor_reco_index_id, delete_factor_reco_index_if_exists)
    _delete_statement_recommendation_index(statement_reco_index_id, delete_statement_reco_index_if_exists)
    _create_factor_recommendation_index(factor_reco_index_id)
    _create_statement_recommendation_index(statement_reco_index_id)


def _delete_factor_recommendation_index(factor_reco_index_id, delete_factor_reco_index_if_exists):
    es_client = es_service.get_client()

    if es_client.indices.exists(index=factor_reco_index_id) and delete_factor_reco_index_if_exists is True:
        print('Deleting factor recommendation index!')
        es_client.indices.delete(index=factor_reco_index_id)


def _delete_statement_recommendation_index(statement_reco_index_id, delete_statement_reco_index_if_exists):
    es_client = es_service.get_client()

    if es_client.indices.exists(index=statement_reco_index_id) and delete_statement_reco_index_if_exists is True:
        print('Deleting statement recommendation index!')
        es_client.indices.delete(index=statement_reco_index_id)


def _create_factor_recommendation_index(factor_reco_index_id):
    es_client = es_service.get_client()

    if es_client.indices.exists(index=factor_reco_index_id) is False:
        print('Creating factor recommendation index mapping')
        es_client.indices.create(
            index=factor_reco_index_id,
            body={
                'mappings': es_recommendations_helper.get_factor_recommendation_index_mapping()
            }
        )


def _create_statement_recommendation_index(statement_reco_index_id):
    es_client = es_service.get_client()

    if es_client.indices.exists(index=statement_reco_index_id) is False:
        print('Creating statement recommendation index mapping')
        es_client.indices.create(
            index=statement_reco_index_id,
            body={
                'mappings': es_recommendations_helper.get_statement_recommendation_index_mapping()
            }
        )
