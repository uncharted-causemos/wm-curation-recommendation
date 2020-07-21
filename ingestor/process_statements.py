import os
from collections import deque
from elasticsearch.helpers import parallel_bulk
from services import embedding_service, es_service


def process():
    es_client = es_service.get_client()

    # Get ES Record cursor
    data = es_client.search(
        index=os.getenv('KB_INDEX_NAME'),
        size=10000,
        scroll='10m',
        _source_includes=['subj.factor', 'obj.factor'],  # TODO: Change this to be the full statement from evidence
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
        deque(parallel_bulk(es_client, _process_statements(data['hits']['hits'])), maxlen=0)

        total_documents_processed = total_documents_processed + scroll_size

        data = es_client.scroll(scroll_id=sid, scroll='10m')
        sid = data['_scroll_id']
        scroll_size = len(data['hits']['hits'])

    es_client.indices.refresh(index=es_service.get_statement_index_name(os.getenv('KB_INDEX_NAME')))
    es_client.clear_scroll(scroll_id=sid)


def _process_statements(statements):
    for statement in statements:
        # TODO: Change this to be the full statement from evidence
        yield _build_statement(statement['_source']['subj']['factor'] + " " + statement['_source']['obj']['factor'])


def _build_statement(statement_text_original):
    statement_text_cleaned = embedding_service.clean(statement_text_original)
    return {
        '_op_type': 'index',
        '_index': es_service.get_statement_index_name(os.getenv('KB_INDEX_NAME')),
        '_id': hash(statement_text_original),  # TODO: This could be made more resilient by using something that's consistent across python runs?
        '_source': {
            'statement_vector_300_d': embedding_service.compute_normalized_vector(statement_text_cleaned).tolist(),
            'statement_vector_20_d': [],
            'statement_vector_2_d': [],
            'statement_text_cleaned': statement_text_cleaned,
            'statement_text_original': statement_text_original
        }
    }
