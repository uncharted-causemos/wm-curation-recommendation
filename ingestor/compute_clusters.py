from services import clustering_service, es_service
from helpers.es import es_recommendations_helper
from helpers import utils
from elasticsearch.helpers import bulk
import os


def compute_and_update(dim, min_cluster_size, min_samples, cluster_selection_epsilon, entity_type):
    deduped_recommendations = _get_all_recommendations_deduped(dim, entity_type)
    cluster_ids = _compute_clusters(deduped_recommendations, dim, min_cluster_size, min_samples, cluster_selection_epsilon)
    deduped_recommendations = _assign_cluster_ids_to_recommendations(deduped_recommendations, cluster_ids)
    _update(deduped_recommendations)


def _get_all_recommendations_deduped(dim, entity_type):
    recommendation_index_name = es_service.get_recommendation_index_name(os.getenv('KB_INDEX_NAME'))
    recommendation_vector_field_name = es_recommendations_helper.get_vector_field_name(dim)
    recos = es_recommendations_helper.get_all_recommendations(recommendation_index_name, source_fields=[
                                                              'text_cleaned', recommendation_vector_field_name], entity_type=entity_type)
    recos = es_recommendations_helper.map_vector(recos, dim)
    recos = utils.dedupe_recommendations(recos, 'text_cleaned')
    return recos


def _compute_clusters(reco_vectors, dim, min_cluster_size, min_samples, cluster_selection_epsilon):
    reco_vector_matrix = utils.build_reco_vector_matrix(reco_vectors)
    return clustering_service.compute_clusters(reco_vector_matrix, min_cluster_size, min_samples, cluster_selection_epsilon)


def _assign_cluster_ids_to_recommendations(recos, cluster_ids):
    for idx, f in enumerate(recos):
        f['cluster_id'] = cluster_ids[idx]
    return recos


def _update(deduped_recos):
    print('Updating cluster ids for all recommendations')
    es_client = es_service.get_client()
    bulk(es_client, _build_update_query(deduped_recos))
    es_service.get_client().indices.refresh(index=es_service.get_recommendation_index_name(os.getenv('KB_INDEX_NAME')))
    print('Finished updating cluster ids for all recommendations')


def _build_update_query(deduped_recos):
    for f in deduped_recos:
        for f_id in f['id']:
            yield {
                '_op_type': 'update',
                '_index': es_service.get_recommendation_index_name(os.getenv('KB_INDEX_NAME')),
                '_id': f_id,
                'doc': {
                    'cluster_id': f['cluster_id'].item()  # Converting from numpy int to python int
                }
            }
