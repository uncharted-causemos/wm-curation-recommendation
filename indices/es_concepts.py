from services import es_service
import os


def get_all_concepts():
    es_client = es_service.get_client()
    data = es_client.search(
        index=os.getenv("CONCEPTS_INDEX_NAME"),
        size=10000,
        scroll="2m",
        body={
            "query": {
                "match_all": {}
            }
        }
    )

    sid = data["_scroll_id"]
    scroll_size = len(data["hits"]["hits"])

    concepts = []
    while scroll_size > 0:
        results = data["hits"]["hits"]
        mapped_results = list(map(lambda x: {"concept_vector_300_d": x["_source"]["concept_vector_300_d"], "id": x["_id"]}, results))
        concepts = concepts + mapped_results

        data = es_client.scroll(scroll_id=sid, scroll="2m")
        sid = data["_scroll_id"]
        scroll_size = len(data["hits"]["hits"])

    es_client.clear_scroll(scroll_id=sid)

    return concepts


def get_concept_coord(concept_name):
    es_client = es_service.get_client()
    data = es_client.search(
        index=os.getenv("CONCEPTS_INDEX_NAME"),
        body={
            "_source_includes": ["concept_vector_2_d"],
            "query": {
                "bool": {
                    "filter": {
                        "term": {
                            "concept": concept_name
                        }
                    }
                }
            }
        }
    )

    return data["hits"]["hits"]["_source"]["concept_vector_2_d"]
