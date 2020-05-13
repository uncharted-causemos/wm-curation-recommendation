import os
from collections import deque
from elasticsearch.helpers import parallel_bulk
from services import embedding_service, es_service


def process():
    es_client = es_service.get_client()

    # Get ES Record cursor
    data = es_client.search(
        index=os.getenv("INCOMING_KB_INDEX_NAME"),
        size=10000,
        scroll="5m",
        body={
            "query": {
                "match_all": {}
            }
        }
    )

    sid = data["_scroll_id"]
    scroll_size = len(data["hits"]["hits"])

    total_documents_processed = 0

    # Iterate over all documents
    while scroll_size > 0:
        print(r"Processing statements from {total_documents_processed} to {total_documents_processed + scroll_size}")
        # TODO: Log failed entries
        deque(parallel_bulk(es_client, _process_statements_into_factors(data["hits"]["hits"])), maxlen=0)

        total_documents_processed = total_documents_processed + scroll_size

        data = es_client.scroll(scroll_id=sid, scroll="2m")
        sid = data["_scroll_id"]
        scroll_size = len(data["hits"]["hits"])

    es_client.indices.refresh(index=os.getenv("OUTGOING_KB_INDEX_NAME"))
    es_client.clear_scroll(scroll_id=sid)


def _process_statements_into_factors(statements):
    for statement in statements:
        statement_id = statement["_source"]["id"]
        yield _build_factor(statement["_source"]["subj"], "subj", statement_id)
        yield _build_factor(statement["_source"]["obj"], "obj", statement_id)


def _build_factor(factor, factor_type, statement_id):
    factor_text_cleaned = embedding_service.clean(factor["factor"])
    # TODO: concept candidates
    return {
        "_op_type": "index",
        "_index": os.getenv("OUTGOING_KB_INDEX_NAME"),
        "_source": {
            "factor_vector_300_d": embedding_service.compute_normalized_vector(factor_text_cleaned).tolist(),
            "concept": factor["concept"],
            "type": factor_type,
            "polarity": factor["polarity"],
            "statement_id": statement_id,
            "factor_cleaned": factor_text_cleaned,
            "factor_vector_2_d": []
        }
    }
