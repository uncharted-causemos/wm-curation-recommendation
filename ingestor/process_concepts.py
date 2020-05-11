import os
from elasticsearch.helpers import bulk
import services.factor_embedding_service as fe_service
import services.elasticsearch_service as es_service
import services.ontology_service as ont_service
from numpy import linalg as LA


def process():
    print("Processing concepts.")
    concept_names = ont_service.get_concept_names()
    concept_examples = ont_service.get_concept_examples()
    concept_embeddings = _compute_concept_embeddings(concept_names, concept_examples)
    _index_concepts(concept_names, concept_examples, concept_embeddings)
    print("Finished processing concepts.")


def _index_concepts(concept_names, concept_examples, concept_embeddings):
    es_client = es_service.get_client()
    bulk(es_client, _build_concepts(concept_names, concept_examples, concept_embeddings))
    es_client.indices.refresh(index=os.getenv("concepts_index_name"))


def _build_concepts(concept_names, concept_examples, concept_embeddings):
    for i in range(0, len(concept_names)):
        yield {
            "_op_type": "index",
            "_index": os.getenv("concepts_index_name"),
            "_source": {
                "concept": concept_names[i],
                "examples": concept_examples[i],
                "concept_vector_300_d": concept_embeddings[i],
                "concept_vector_2_d": []
            }
        }


# TODO: Confirm this is how embeddings for concepts should be calculated
def _compute_concept_embeddings(concept_names, concept_examples):
    concept_text_representations = _get_concept_text_representations(concept_names, concept_examples)
    return list(map(lambda x: fe_service.compute_normalized_vector(x).tolist(), concept_text_representations))


def _get_concept_text_representations(concept_names, concept_examples):
    cleaned_concept_names = list(map(lambda x: x[x.rfind('/') + 1:].replace('_', ' '), concept_names))
    flattened_examples = list(map(lambda x: " ".join(x), concept_examples))

    names_and_examples = []
    for i in range(0, len(concept_names)):
        names_and_examples.append(cleaned_concept_names[i] + " " + flattened_examples[i])

    return names_and_examples
