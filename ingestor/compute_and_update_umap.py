import os
from elasticsearch.helpers import bulk
from es_helpers import es_factors_helper, es_concepts_helper
from services import dimension_reduction_service, es_service
import numpy as np


def compute_and_update():
    concepts, factors = _get_all_concepts_and_factors()
    concept_vectors_2_d, factor_vectors_2_d = _compute(concepts, factors)
    _update_factors(factors, factor_vectors_2_d)
    _update_concepts(concepts, concept_vectors_2_d)


def _get_all_concepts_and_factors():
    print('Fetching all vectors for umap.')
    concepts = es_concepts_helper.get_all_concepts()
    factors = es_factors_helper.get_all_factors(os.getenv('OUTGOING_KB_INDEX_NAME'))
    print('Finished fetching all vectors for umap.')
    return (concepts, factors)


def _compute(concepts, factors):
    print('Computing umap for all concepts and factors.')
    concept_vectors_300_d = np.asmatrix(np.array(list(map(lambda x: x['concept_vector_300_d'], concepts))))
    factor_vectors_300_d = np.asmatrix(np.array(list(map(lambda x: x['factor_vector_300_d'], factors))))

    print('Concept vectors shape is: {}'.format(concept_vectors_300_d.shape))
    print('Factor vectors shape is: {}'.format(factor_vectors_300_d.shape))

    mapper = dimension_reduction_service.fit(np.concatenate([concept_vectors_300_d, factor_vectors_300_d]))
    concept_vectors_2_d = dimension_reduction_service.transform(mapper, concept_vectors_300_d)
    factor_vectors_2_d = dimension_reduction_service.transform(mapper, factor_vectors_300_d)

    if len(factors) != len(factor_vectors_2_d):
        raise AssertionError  # TODO: Fix
    if len(concepts) != len(concept_vectors_2_d):
        raise AssertionError  # TODO: Fix

    print('Finished computing umap for all concepts and factors.')
    return (concept_vectors_2_d, factor_vectors_2_d)


def _update_factors(factors, factor_vector_2_d):
    es_client = es_service.get_client()
    print('Updating factors with 2_d vectors.')
    bulk(es_client, _build_factor_update(factors, factor_vector_2_d))
    print('Finished updating factors with 2_d vectors.')


def _build_factor_update(factors, factor_vectors_2_d):
    for i in range(0, len(factors)):
        yield {
            '_op_type': 'update',
            '_index': os.getenv('OUTGOING_KB_INDEX_NAME'),
            '_id': factors[i]['id'],
            'doc': {
                'factor_vector_2_d': factor_vectors_2_d[i].tolist()
            }
        }


def _update_concepts(concepts, concept_vectors_2_d):
    es_client = es_service.get_client()
    print('Updating concepts with 2_d vectors.')
    bulk(es_client, _build_concept_update(concepts, concept_vectors_2_d))
    print('Finished updating concepts with 2_d vectors.')


def _build_concept_update(concepts, concept_vectors_2_d):
    for i in range(0, len(concepts)):
        yield {
            '_op_type': 'update',
            '_index': os.getenv('CONCEPTS_INDEX_NAME'),
            '_id': concepts[i]['id'],
            'doc': {
                'concept_vector_2_d': concept_vectors_2_d[i].tolist()
            }
        }
