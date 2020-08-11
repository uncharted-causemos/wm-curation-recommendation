from collections import deque
from elasticsearch.helpers import parallel_bulk
from services import embedding_service, es_service


def process(kb_index_id, factor_reco_index_id, statement_reco_index_id):
    es_client = es_service.get_client()

    # Get ES Record cursor
    data = es_client.search(
        index=kb_index_id,
        size=10000,
        scroll='10m',
        _source_includes=['subj.factor', 'obj.factor'],
        body={
            'query': {
                'match_all': {}
            }
        }
    )

    sid = data['_scroll_id']
    scroll_size = len(data['hits']['hits'])

    total_documents_processed = 0

    # Iterate over all documents
    while scroll_size > 0:
        print(f'Processing statements from {total_documents_processed} to {total_documents_processed + scroll_size}')
        # TODO: Log failed entries
        deque(parallel_bulk(es_client, _process_statements(data['hits']['hits'], factor_reco_index_id, statement_reco_index_id)), maxlen=0)

        total_documents_processed = total_documents_processed + scroll_size

        data = es_client.scroll(scroll_id=sid, scroll='10m')
        sid = data['_scroll_id']
        scroll_size = len(data['hits']['hits'])

    es_client.indices.refresh(index=factor_reco_index_id)
    es_client.indices.refresh(index=statement_reco_index_id)
    es_client.clear_scroll(scroll_id=sid)


def _process_statements(statements, factor_reco_index_id, statement_reco_index_id):
    for statement in statements:
        yield _build_factor_recommendation(statement['_source']['subj']['factor'], factor_reco_index_id)
        yield _build_factor_recommendation(statement['_source']['obj']['factor'], factor_reco_index_id)
        yield _build_statement_recommendation(statement['_source'], statement_reco_index_id)


"""
It is possible that the cleaned versions of different factor texts are the same. 
For example, "The conflict" and "A conflict" will both result in "conflict" after they've been processed.

It is also possible that the knowledgebase contains multiple factors that are the same.
For example, there might be a statement {subj_factor: A famine, obj_factor: food scarcity}, and a statement {subj_factor: low rainfall, obj_factor: A famine}
If we blindly index each factor we will have duplicate documents, which down the line may cause unexpected results. 

Elasticsearch doesn't have the concept of a unique field. Therefore, to ensure that there is only one document per unprocessed factor text, 
the id is calculated using a hash function with the key as the original unprocessed factor text.
"""


def _build_factor_recommendation(text_original, factor_reco_index_id):
    text_cleaned = embedding_service.clean(text_original)
    return {
        '_op_type': 'index',
        '_index': factor_reco_index_id,
        '_id': hash(text_original),
        '_source': {
            'vector_300_d': embedding_service.compute_normalized_vector(text_cleaned).tolist(),
            'text_cleaned': text_cleaned,
            'text_original': text_original
        }
    }


def _build_statement_recommendation(statement_source, statement_reco_index_id):
    text_original = statement_source['subj']['factor'] + " " + statement_source['obj']['factor']
    text_cleaned = embedding_service.clean(text_original)
    return {
        '_op_type': 'index',
        '_index': statement_reco_index_id,
        '_id': hash(text_original),
        '_source': {
            'vector_300_d': embedding_service.compute_normalized_vector(text_cleaned).tolist(),
            'text_cleaned': text_cleaned,
            'text_original': text_original,
            'subj_factor': statement_source['subj']['factor'],
            'obj_factor': statement_source['obj']['factor']
        }
    }
