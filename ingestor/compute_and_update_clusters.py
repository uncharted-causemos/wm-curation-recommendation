import services.ontology_service as ont_service
import services.clusters_service as clusters_service
import services.elasticsearch_service as es_service
import services.factors_service as factors_service
from elasticsearch.helpers import bulk
import os


def compute_and_update():
    concept_names = ont_service.get_concept_names()
    index_name = os.getenv("outgoing_kb_index_name")
    for cn in concept_names:
        results = factors_service.get_all_factors_for_concept(index_name, cn)
        if len(results) == 0:
            print("No factors were associated with concept {}. Skipping...".format(cn))
            continue
        factor_df = _compute(cn, results)
        _update(cn, factor_df)


def _compute(concept_name, results):
    return clusters_service.compute_clusters(concept_name, results)


def _update(concept_name, factor_df):
    print("Updating cluster ids for concept {}".format(concept_name))
    es_client = es_service.get_client()
    bulk(es_client, _build_update_query(factor_df))
    print("Finished updating cluster ids for concept {}".format(concept_name))


def _build_update_query(factor_df):
    for index, row in factor_df.iterrows():
        for doc_id in row["id"]:
            yield {
                "_op_type": "update",
                "_index": os.getenv("outgoing_kb_index_name"),
                "_id": doc_id,
                "doc": {
                    "cluster_id": row["cluster_id"]
                }
            }
