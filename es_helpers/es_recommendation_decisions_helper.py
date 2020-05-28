import os
from services import es_service

_recommendation_decisions_index_mapping = {
    'properties': {
        'curation_type': {'type': 'keyword'},
        'kb_id': {'type': 'keyword'},
        'project_id': {'type': 'keyword'},
        'curation': {'type': 'nested'},  # Keeping this open as it'll vary depending on the type of curation
        'recommendations': {'type': 'nested'}  # Keeping this open as it'll vary depending on the type of curation
    }
}


def get_recommendation_decisions_index_mapping():
    return _recommendation_decisions_index_mapping


def insert_recommendation_decisions(recommendation_decisions):
    # FIXME: Consider passing back errors from parallel_bulk
    es_client = es_service.get_client()
    es_client.index(
        index=os.getenv('RECOMMENDATION_DECISIONS_INDEX_NAME'),
        body=recommendation_decisions
    )


def _recommendation_decisions_insert_generator(recommendation_decisions):
    for rd in recommendation_decisions:
        yield {
            '_op_type': 'index',
            '_index': os.getenv('RECOMMENDATION_DECISIONS_INDEX_NAME'),
            '_source': rd
        }
