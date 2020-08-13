from services import es_service


_factor_recommendation_index_mapping = {
    'properties': {
        'text_original': {'type': 'keyword'},
        'text_cleaned': {'type': 'keyword'},
        'cluster_id': {'type': 'integer'},
        'vector_300_d': {'type': 'dense_vector', 'dims': 300},
        'vector_20_d': {'type': 'dense_vector', 'dims': 20},
        'vector_2_d': {'type': 'dense_vector', 'dims': 2}
    }
}

_statement_recommendation_index_mapping = {
    'properties': {
        'text_original': {'type': 'keyword'},
        'text_cleaned': {'type': 'keyword'},
        'cluster_id': {'type': 'integer'},
        'vector_300_d': {'type': 'dense_vector', 'dims': 300},
        'vector_20_d': {'type': 'dense_vector', 'dims': 20},
        'vector_2_d': {'type': 'dense_vector', 'dims': 2},
        'subj_factor': {'type': 'keyword'},
        'obj_factor': {'type': 'keyword'}
    }
}


def get_dim_vector_field_name(dim):
    return f'vector_{dim}_d'


def get_factor_recommendation_index_mapping():
    return _factor_recommendation_index_mapping


def get_statement_recommendation_index_mapping():
    return _statement_recommendation_index_mapping


def get_factor_recommendation_index_id(kb_id):
    return 'curation_factor_recommendations_' + kb_id


def get_statement_recommendation_index_id(kb_id):
    return 'curation_statement_recommendations_' + kb_id


def map_vector(recommendations, dim):
    vector_field_name = get_dim_vector_field_name(dim)

    def _map(reco):
        reco['vector'] = reco[vector_field_name]
        return reco

    return list(map(_map, recommendations))


def get_all_recommendations(source_fields, recommendation_index_id):

    def _map_reco_source(reco_doc):
        reco = reco_doc['_source']
        reco['id'] = reco_doc['_id']
        return reco

    es_client = es_service.get_client()
    data = es_client.search(
        index=recommendation_index_id,
        size=10000,
        scroll='2m',
        _source_includes=source_fields,
        body={
            'query': {
                'match_all': {}
            }
        }
    )

    sid = data['_scroll_id']
    scroll_size = len(data['hits']['hits'])

    recos = []
    while scroll_size > 0:
        recos = recos + data['hits']['hits']

        data = es_client.scroll(scroll_id=sid, scroll='2m')
        sid = data['_scroll_id']
        scroll_size = len(data['hits']['hits'])

    es_client.clear_scroll(scroll_id=sid)
    mapped_recos = list(map(_map_reco_source, recos))
    return mapped_recos


def get_recommendations_in_same_cluster(cluster_id, clustering_dim, recommendation_index_id):
    vector_field_name = get_dim_vector_field_name(clustering_dim)

    def _map_source(reco_doc):
        reco = reco_doc['_source']
        reco['vector'] = reco[vector_field_name]
        reco.pop(vector_field_name, None)
        return reco

    es_client = es_service.get_client()
    data = es_client.search(
        index=recommendation_index_id,
        size=10000,
        scroll='5m',
        _source_includes=['text_original', 'text_cleaned', vector_field_name],
        body={
            'query': {
                'bool': {
                    'filter': [
                        {'term': {'cluster_id': cluster_id}}
                    ]
                }
            }
        }
    )

    sid = data['_scroll_id']
    scroll_size = len(data['hits']['hits'])

    results = []
    while scroll_size > 0:
        results = results + list(map(_map_source, data['hits']['hits']))

        data = es_client.scroll(scroll_id=sid, scroll='2m')
        sid = data['_scroll_id']
        scroll_size = len(data['hits']['hits'])

    es_client.clear_scroll(scroll_id=sid)
    print(f'Finished fetching all recommendations for cluster {cluster_id}')
    return results


def get_recommendation(text_original, recommendation_index_id):
    es_client = es_service.get_client()
    data = es_client.search(
        index=recommendation_index_id,
        size=1,
        scroll='5m',
        body={
            'query': {
                'bool': {
                    'filter': [
                        {'term': {'text_original': text_original}}
                    ]
                }
            }
        }
    )

    docs = data['hits']['hits']
    if len(docs) < 1:
        raise AssertionError(f'Unable to find doc with text_original: {text_original} in index: {recommendation_index_id}')

    return docs[0]['_source']
