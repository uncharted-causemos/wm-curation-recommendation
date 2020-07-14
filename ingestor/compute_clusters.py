from services import clustering_service, es_service, utils
from es_helpers import es_factors_helper
from elasticsearch.helpers import bulk
import os


def compute_and_update(dim):
    factors = _get_all_factors(dim)
    cluster_ids = _compute_clusters(factors, dim)
    factors = _assign_cluster_ids_to_factors(factors, cluster_ids)
    _update(factors)


def _get_all_factors(dim):
    factor_index_name = es_service.get_factor_index_name(os.getenv('KB_INDEX_NAME'))
    factors = es_factors_helper.get_all_factor_vectors(factor_index_name, dim)
    return factors


def _compute_clusters(factor_vectors, dim):
    factor_vector_matrix = utils.build_factor_vector_matrix(factor_vectors)
    return clustering_service.compute_clusters(factor_vector_matrix)


def _assign_cluster_ids_to_factors(factors, cluster_ids):
    for idx, f in enumerate(factors):
        f['cluster_id'] = cluster_ids[idx]
    return factors


def _update(factors):
    print('Updating cluster ids for all factors')
    es_client = es_service.get_client()
    bulk(es_client, _build_update_query(factors))
    es_service.get_client().indices.refresh(index=es_service.get_factor_index_name(os.getenv('KB_INDEX_NAME')))
    print('Finished updating cluster ids for all factors')


def _build_update_query(factors):
    for f in factors:
        yield {
            '_op_type': 'update',
            '_index': es_service.get_factor_index_name(os.getenv('KB_INDEX_NAME')),
            '_id': f['id'],
            'doc': {
                'cluster_id': f['cluster_id']
            }
        }
