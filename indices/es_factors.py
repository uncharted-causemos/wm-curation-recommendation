from services import es_service


def get_all_factors_for_concept(index_name, concept_name):
    print("Fetching all factors for concept: {}".format(concept_name))
    es_client = es_service.get_client()

    data = es_client.search(
        index=index_name,
        size=10000,
        scroll="10m",
        body={
            "_source": ["factor_vector_2_d", "factor_cleaned"],
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

    sid = data["_scroll_id"]
    scroll_size = len(data["hits"]["hits"])

    results = []
    while scroll_size > 0:
        results = results + data["hits"]["hits"]

        data = es_client.scroll(scroll_id=sid, scroll="2m")
        sid = data["_scroll_id"]
        scroll_size = len(data["hits"]["hits"])

    es_client.clear_scroll(scroll_id=sid)
    print("Finished fetching all concepts for {}".format(concept_name))
    return results


def get_all_factors(index_name):
    es_client = es_service.get_client()
    data = es_client.search(
        index=index_name,
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

    factors = []
    while scroll_size > 0:
        results = data["hits"]["hits"]
        mapped_results = list(map(lambda x: {"factor_vector_300_d": x["_source"]["factor_vector_300_d"], "id": x["_id"]}, results))
        factors = factors + mapped_results

        data = es_client.scroll(scroll_id=sid, scroll="2m")
        sid = data["_scroll_id"]
        scroll_size = len(data["hits"]["hits"])

    es_client.clear_scroll(scroll_id=sid)

    return factors
