from services import es_service


def get_all_factors_with_cluster_id(index_name, concept, cluster_id, statement_subspace):
    es_client = es_service.get_client()
    data = es_client.search(
        index=index_name,
        body={
            'query': {
                'bool': {
                    'filter': {
                        'term': {
                            'concept': concept
                        },
                        'term': {
                            'cluster_id': cluster_id
                        },
                    },
                    'filter': {
                        'terms': {
                            'statement_id': statement_subspace
                        }
                    }
                }
            }
        }
    )
    return list(map(lambda x: x['_source'], data['hits']['hits']))


def get_all_factors_with_statement_ids(index_name, statement_ids, statement_subspace):
    statement_id_filter = set(statement_ids).intersection(set(statement_subspace))
    if len(statement_id_filter) == 0:
        return []

    es_client = es_service.get_client()
    data = es_client.search(
        index=index_name,
        _source_includes=['statement_id', 'type'],
        body={
            'query': {
                'bool': {
                    'filter': {
                        'terms': {
                            'statement_id': statement_ids
                        }
                    }
                }
            }
        }
    )
    return list(map(lambda x: x['_source'], data['hits']['hits']))


def get_all_factors_within_concept_score_threshold(index_name, new_concept, existing_concept, score_threshold):
    # TODO: Implement
    pass


def get_statement_ids_with_doc_ids(index_name, doc_id):
    es_client = es_service.get_client()
    data = es_client.search(
        index=index_name,
        size=1,
        _source_includes=['indra_id'],
        body={
            'nested': {
                'path': 'evidences',
                'query': {
                    'bool': {
                        'must': [
                            {
                                'match': {
                                    'evidences.document_context.doc_id': doc_id
                                }
                            }
                        ]
                    }
                }
            }
        }
    )

    return list(map(lambda x: x['_source']['indra_id'], data['hits']['hits']))


def get_number_evidences(index_name, statement_id, factor_type):
    es_client = es_service.get_client()
    data = es_client.search(
        index=index_name,
        size=1,
        _source_includes=['wm.num_evidence'],
        body={
            'query': {
                'bool': {
                    'filter': {
                        'term': {
                            'id': statement_id
                        }
                    }
                }
            }
        }
    )

    return data['hits']['hits'][0]['_source']['wm']['num_evidence']


def get_statement_doc_id(index_name, statement_id, factor_type):
    es_client = es_service.get_client()
    data = es_client.search(
        index=index_name,
        size=1,
        _source_includes=['evidences'],
        body={
            'query': {
                'bool': {
                    'filter': {
                        'term': {
                            'indra_id': statement_id
                        }
                    }
                }
            }
        }
    )

    return data['hits']['hits'][0]['_source']['evidences'][0]['document_context']['doc_id']
