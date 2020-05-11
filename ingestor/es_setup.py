import services.elasticsearch_service as es_service
import os


def setup_outgoing_kb_index():
    es_client = es_service.get_client()
    outgoing_kb_index_name = os.getenv("outgoing_kb_index_name")
    # TODO: Move this deletion logic somewhere
    if es_client.indices.exists(index=outgoing_kb_index_name) and os.getenv("delete_outgoing_kb_index_if_exists") == "true":
        es_client.indices.delete(index=outgoing_kb_index_name)

    # TODO: Move this creation logic somewhere
    if es_client.indices.exists(index=outgoing_kb_index_name) is False:
        es_client.indices.create(
            index=outgoing_kb_index_name,
            body={
                "mappings": {
                    "properties": {
                        "concept": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "factor_cleaned": {"type": "keyword"},
                        "statement_id": {"type": "keyword"},
                        "cluster_id": {"type": "integer"},
                        "polarity": {"type": "integer"}
                    }
                }
            }
        )


def setup_concept_index():
    es_client = es_service.get_client()
    concepts_index_name = os.getenv("concepts_index_name")
    if es_client.indices.exists(index=concepts_index_name) and os.getenv("delete_concepts_index_if_exists") == "true":
        es_client.indices.delete(index=concepts_index_name)

    if es_client.indices.exists(index=concepts_index_name) is False:
        es_client.indices.create(
            index=concepts_index_name,
            body={
                "mappings": {
                    "properties": {
                        "concept": {"type": "keyword"}
                    }
                }
            }
        )
