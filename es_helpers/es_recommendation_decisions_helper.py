import os
from collections import deque
from elasticsearch.helpers import parallel_bulk
from services import es_service


def insert_recommendation_decisions(recommendation_decisions):
    # FIXME: Consider passing back errors from parallel_bulk
    es_client = es_service.get_client()
    deque(parallel_bulk(es_client, _recommendation_decisions_insert_generator(recommendation_decisions)), maxlen=0)


def _recommendation_decisions_insert_generator(recommendation_decisions):
    for rd in recommendation_decisions:
        yield {
            '_op_type': 'index',
            '_index': os.getenv('RECOMMENDATION_DECISIONS_INDEX_NAME'),
            '_source': rd
        }
