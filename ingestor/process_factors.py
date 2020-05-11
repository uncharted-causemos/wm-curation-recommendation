import os
from elasticsearch.helpers import bulk
import services.factor_embedding_service as fe_service
import services.elasticsearch_service as es_service
from numpy import linalg as LA


def process():
    es_client = es_service.get_client()

    # Get ES Record cursor
    data = es_client.search(
        index=os.getenv("incoming_kb_index_name"),
        size=10000,
        scroll="5m",
        body={
            "query": {
                "match_all": {}
            }
        }
    )

    sid = data['_scroll_id']
    scroll_size = len(data['hits']['hits'])

    total_documents_processed = 0

    # Iterate over all documents
    while scroll_size > 0:
        print("Processing documents from {} to {}".format(total_documents_processed, total_documents_processed + scroll_size))
        bulk(es_client, _process_statements_into_factors(data['hits']['hits']))

        total_documents_processed = total_documents_processed + scroll_size

        data = es_client.scroll(scroll_id=sid, scroll="2m")
        sid = data['_scroll_id']
        scroll_size = len(data['hits']['hits'])

    es_client.indices.refresh(index=os.getenv("outgoing_kb_index_name"))
    es_client.clear_scroll(scroll_id=sid)


def _process_statements_into_factors(statements):
    for statement in statements:
        statement_id = statement["_source"]["id"]
        yield _build_factor(statement["_source"]["subj"], "subj", statement_id)
        yield _build_factor(statement["_source"]["obj"], "obj", statement_id)


def _build_factor(factor, factor_type, statement_id):
    factor_text_cleaned = fe_service.clean(factor["factor"])
    # TODO: concept candidates
    return {
        "_op_type": "index",
        "_index": os.getenv("outgoing_kb_index_name"),
        "_source": {
            "factor_vector_300_d": fe_service.compute_normalized_vector(factor_text_cleaned).tolist(),
            "concept": factor["concept"],
            "type": factor_type,
            "polarity": factor["polarity"],
            "statement_id": statement_id,
            "factor_cleaned": factor_text_cleaned,
            "factor_vector_2_d": []
        }
    }
