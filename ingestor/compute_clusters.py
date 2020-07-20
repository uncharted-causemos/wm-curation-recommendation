from services import clustering_service, es_service
from helpers.es import es_factors_helper
from helpers import utils
from elasticsearch.helpers import bulk
import os


def compute_and_update(dim, min_cluster_size, min_samples, cluster_selection_epsilon):
    deduped_factors = _get_all_factors_deduped(dim)
    cluster_ids = _compute_clusters(deduped_factors, dim, min_cluster_size, min_samples, cluster_selection_epsilon)
    deduped_factors = _assign_cluster_ids_to_factors(deduped_factors, cluster_ids)
    _update(deduped_factors)


def _get_all_factors_deduped(dim):
    factor_index_name = es_service.get_factor_index_name(os.getenv('KB_INDEX_NAME'))
    factor_vector_field_name = es_factors_helper.get_factor_vector_field_name(dim)
    factors = es_factors_helper.get_all_factors(factor_index_name, source_fields=['factor_text_cleaned', factor_vector_field_name])
    factors = es_factors_helper.map_factor_vector(factors, dim)
    factors = utils.dedupe_factors(factors, 'factor_text_cleaned')
    return factors


def _compute_clusters(factor_vectors, dim, min_cluster_size, min_samples, cluster_selection_epsilon):
    factor_vector_matrix = utils.build_factor_vector_matrix(factor_vectors)
    return clustering_service.compute_clusters(factor_vector_matrix, min_cluster_size, min_samples, cluster_selection_epsilon)


def _assign_cluster_ids_to_factors(factors, cluster_ids):
    for idx, f in enumerate(factors):
        f['cluster_id'] = cluster_ids[idx]
    return factors


def _update(deduped_factors):
    print('Updating cluster ids for all factors')
    es_client = es_service.get_client()
    bulk(es_client, _build_update_query(deduped_factors))
    es_service.get_client().indices.refresh(index=es_service.get_factor_index_name(os.getenv('KB_INDEX_NAME')))
    print('Finished updating cluster ids for all factors')


def _build_update_query(deduped_factors):
    for f in deduped_factors:
        for f_id in f['id']:
            yield {
                '_op_type': 'update',
                '_index': es_service.get_factor_index_name(os.getenv('KB_INDEX_NAME')),
                '_id': f_id,
                'doc': {
                    'cluster_id': f['cluster_id']
                }
            }
