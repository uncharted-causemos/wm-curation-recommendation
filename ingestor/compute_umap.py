import os
from elasticsearch.helpers import bulk
from services import dimension_reduction_service, es_service
from helpers.es import es_factors_helper
from helpers import utils
import numpy as np


def compute_and_update(dim_start, dim_end, min_dist):
    deduped_factors = _get_all_factors(dim_start)
    factor_vectors_x_d = _compute_umap(deduped_factors, dim_end, min_dist)
    _update_factors(deduped_factors, factor_vectors_x_d, dim_end)


def _get_all_factors(dim):
    factor_index_name = es_service.get_factor_index_name(os.getenv('KB_INDEX_NAME'))
    factor_vector_field_name = es_factors_helper.get_factor_vector_field_name(dim)
    factors = es_factors_helper.get_all_factors(factor_index_name, source_fields=['factor_text_cleaned', factor_vector_field_name])
    factors = es_factors_helper.map_factor_vector(factors, dim)
    factors = utils.dedupe_factors(factors, 'factor_text_cleaned')
    return factors


def _compute_umap(factors, dim, min_dist):
    print('Computing umap for all concepts and factors.')
    factor_vector_matrix = utils.build_factor_vector_matrix(factors)

    mapper = dimension_reduction_service.fit(factor_vector_matrix, n_components=dim, min_dist=min_dist)
    factor_vectors_x_d = dimension_reduction_service.transform(mapper, factor_vector_matrix)  # TODO: Save the mapper on disk somewhere?

    if len(factors) != len(factor_vectors_x_d):
        raise AssertionError  # TODO: Fix

    print('Finished computing umap for all factors.')
    return factor_vectors_x_d


def _update_factors(deduped_factors, factor_vectors_x_d, dim):
    es_client = es_service.get_client()
    print(f'Updating factors with {dim} dimensional vectors.')
    bulk(es_client, _build_factor_update(deduped_factors, factor_vectors_x_d, dim))
    es_service.get_client().indices.refresh(index=es_service.get_factor_index_name(os.getenv('KB_INDEX_NAME')))
    print(f'Finished updating factors with {dim} dimensional vectors.')


def _build_factor_update(deduped_factors, factor_vectors_x_d, dim):
    factor_vector_field_name = es_factors_helper.get_factor_vector_field_name(dim)
    for idx, f in enumerate(deduped_factors):
        for f_id in f['id']:
            factor_update = {
                '_op_type': 'update',
                '_index': es_service.get_factor_index_name(os.getenv('KB_INDEX_NAME')),
                '_id': f_id,
                'doc': {}
            }
            factor_update['doc'][factor_vector_field_name] = factor_vectors_x_d[idx].tolist()
            yield factor_update
