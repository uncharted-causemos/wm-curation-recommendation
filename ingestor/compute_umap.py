from elasticsearch.helpers import bulk
from services import dimension_reduction_service, es_service
from helpers.es import es_recommendations_helper
from helpers import utils


def compute_and_update(dim_start, dim_end, min_dist, reco_index_id):
    deduped_recommendations = _get_all_recommendations(dim_start, reco_index_id)
    vectors_x_d = _compute_umap(deduped_recommendations, dim_end, min_dist)
    _update_recommendations(deduped_recommendations, vectors_x_d, dim_end, reco_index_id)


def _get_all_recommendations(dim, reco_index_id):
    vector_field_name = es_recommendations_helper.get_dim_vector_field_name(dim)
    recos = es_recommendations_helper.get_all_recommendations(reco_index_id, source_fields=['text_cleaned', vector_field_name])
    recos = es_recommendations_helper.map_vector(recos, dim)
    recos = utils.dedupe_recommendations(recos, 'text_cleaned')
    return recos


def _compute_umap(recos, dim, min_dist):
    print('Computing umap for all recommendations.')
    reco_vector_matrix = utils.build_reco_vector_matrix(recos)

    mapper = dimension_reduction_service.fit(reco_vector_matrix, n_components=dim, min_dist=min_dist)
    reco_vectors_x_d = dimension_reduction_service.transform(mapper, reco_vector_matrix)  # TODO: Save the mapper on disk somewhere?

    if len(recos) != len(reco_vectors_x_d):
        raise AssertionError  # TODO: Fix

    print('Finished computing umap for all recommendations.')
    return reco_vectors_x_d


def _update_recommendations(deduped_recommendations, reco_vectors_x_d, dim, reco_index_id):
    es_client = es_service.get_client()
    print(f'Updating recommendations with {dim} dimensional vectors.')
    bulk(es_client, _build_reco_update(deduped_recommendations, reco_vectors_x_d, dim, reco_index_id))
    es_service.get_client().indices.refresh(index=reco_index_id)
    print(f'Finished updating recommendations with {dim} dimensional vectors.')


def _build_reco_update(deduped_recos, reco_vectors_x_d, dim, reco_index_id):
    reco_vector_field_name = es_recommendations_helper.get_dim_vector_field_name(dim)
    for idx, f in enumerate(deduped_recos):
        for f_id in f['id']:
            reco_update = {
                '_op_type': 'update',
                '_index': reco_index_id,
                '_id': f_id,
                'doc': {}
            }
            reco_update['doc'][reco_vector_field_name] = reco_vectors_x_d[idx].tolist()
            yield reco_update
