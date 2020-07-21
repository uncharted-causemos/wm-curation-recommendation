from services import clustering_service, es_service
from helpers.es import es_statements_helper
from helpers import utils
from elasticsearch.helpers import bulk
import os


def compute_and_update(dim, min_cluster_size, min_samples, cluster_selection_epsilon):
    deduped_statements = _get_all_statements_deduped(dim)
    cluster_ids = _compute_clusters(deduped_statements, dim, min_cluster_size, min_samples, cluster_selection_epsilon)
    deduped_statements = _assign_cluster_ids_to_statements(deduped_statements, cluster_ids)
    _update(deduped_statements)


def _get_all_statements_deduped(dim):
    statement_index_name = es_service.get_statement_index_name(os.getenv('KB_INDEX_NAME'))
    statement_vector_field_name = es_statements_helper.get_statement_vector_field_name(dim)
    statements = es_statements_helper.get_all_statements(statement_index_name, source_fields=['statement_text_cleaned', statement_vector_field_name])
    statements = es_statements_helper.map_statement_vector(statements, dim)
    statements = utils.dedupe_statements(statements, 'statement_text_cleaned')
    return statements


def _compute_clusters(statement_vectors, dim, min_cluster_size, min_samples, cluster_selection_epsilon):
    statement_vector_matrix = utils.build_statement_vector_matrix(statement_vectors)
    return clustering_service.compute_clusters(statement_vector_matrix, min_cluster_size, min_samples, cluster_selection_epsilon)


def _assign_cluster_ids_to_statements(statements, cluster_ids):
    for idx, f in enumerate(statements):
        f['cluster_id'] = cluster_ids[idx]
    return statements


def _update(deduped_statements):
    print('Updating cluster ids for all statements')
    es_client = es_service.get_client()
    bulk(es_client, _build_update_query(deduped_statements))
    es_service.get_client().indices.refresh(index=es_service.get_statement_index_name(os.getenv('KB_INDEX_NAME')))
    print('Finished updating cluster ids for all statements')


def _build_update_query(deduped_statements):
    for f in deduped_statements:
        for f_id in f['id']:
            yield {
                '_op_type': 'update',
                '_index': es_service.get_statement_index_name(os.getenv('KB_INDEX_NAME')),
                '_id': f_id,
                'doc': {
                    'cluster_id': f['cluster_id']
                }
            }
