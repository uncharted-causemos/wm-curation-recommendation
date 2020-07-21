import os
from elasticsearch.helpers import bulk
from services import dimension_reduction_service, es_service
from helpers.es import es_factors_helper, es_statements_helper
from helpers import utils
import numpy as np


def compute_and_update(dim_start, dim_end, min_dist):
    deduped_statements = _get_all_statements(dim_start)
    statement_vectors_x_d = _compute_umap(deduped_statements, dim_end, min_dist)
    _update_statements(deduped_statements, statement_vectors_x_d, dim_end)


def _get_all_statements(dim):
    statement_index_name = es_service.get_statement_index_name(os.getenv('KB_INDEX_NAME'))
    statement_vector_field_name = es_statements_helper.get_statement_vector_field_name(dim)
    statements = es_statements_helper.get_all_statements(statement_index_name, source_fields=['statement_text_cleaned', statement_vector_field_name])
    statements = es_statements_helper.map_statement_vector(statements, dim)
    statements = utils.dedupe_statements(statements, 'statement_text_cleaned')
    return statements


def _compute_umap(statements, dim, min_dist):
    print('Computing umap for all statements...')
    statement_vector_matrix = utils.build_statement_vector_matrix(statements)

    mapper = dimension_reduction_service.fit(statement_vector_matrix, n_components=dim, min_dist=min_dist)
    statement_vectors_x_d = dimension_reduction_service.transform(mapper, statement_vector_matrix)  # TODO: Save the mapper on disk somewhere?

    if len(statements) != len(statement_vectors_x_d):
        raise AssertionError  # TODO: Fix

    print('Finished computing umap for all statements.')
    return statement_vectors_x_d


def _update_statements(deduped_statements, statement_vectors_x_d, dim):
    es_client = es_service.get_client()
    print(f'Updating statements with {dim} dimensional vectors.')
    bulk(es_client, _build_statement_update(deduped_statements, statement_vectors_x_d, dim))
    es_service.get_client().indices.refresh(index=es_service.get_statement_index_name(os.getenv('KB_INDEX_NAME')))
    print(f'Finished updating statements with {dim} dimensional vectors.')


def _build_statement_update(deduped_statements, statement_vectors_x_d, dim):
    statement_vector_field_name = es_statements_helper.get_statement_vector_field_name(dim)
    for idx, f in enumerate(deduped_statements):
        for f_id in f['id']:
            statement_update = {
                '_op_type': 'update',
                '_index': es_service.get_statement_index_name(os.getenv('KB_INDEX_NAME')),
                '_id': f_id,
                'doc': {}
            }
            statement_update['doc'][statement_vector_field_name] = statement_vectors_x_d[idx].tolist()
            yield statement_update
