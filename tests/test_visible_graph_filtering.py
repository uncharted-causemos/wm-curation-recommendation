from functools import reduce
import json
import os
from services import es_service
from helpers.es import es_recommendations_helper
from helpers.api import recommendations_helper


def _get_largest_cluster(index_id):
    es_client = es_service.get_client()
    data = es_client.search(
        index=index_id,
        size=0,
        body={
            'query': {
                'bool': {
                    'must_not': [
                        {'term': {'cluster_id': -1}}
                    ]
                }
            },
            'aggs': {
                'cluster_id_count': {
                    'histogram': {
                        'field': 'cluster_id',
                        'interval': 1,
                        'order': {'_count': 'desc'}
                    }
                }
            }
        }
    )
    largest_cluster_id = data['aggregations']['cluster_id_count']['buckets'][0]['key']
    return largest_cluster_id


def _get_all_factors_in_cluster(cluster_id, index):
    recos = recommendations_helper.get_recommendations_in_cluster(cluster_id, index)
    return list(map(lambda x: x['text_original'], recos))


def _get_most_occurring_concept_for_all_factors(factors, index_id):
    es_client = es_service.get_client()
    data = es_client.search(
        index=index_id,
        size=10000,
        body={
            'query': {
                'bool': {
                    'should': [
                        {'terms': {'subj.factor': factors}},
                        {'terms': {'obj.factor': factors}}
                    ]
                }
            },
            'aggs': {
                'subj_concept_counts': {
                    'terms': {
                        'field': 'subj.concept'
                    }
                },
                'obj_concept_counts': {
                    'terms': {
                        'field': 'obj.concept'
                    }
                }
            }
        }
    )

    concept_counts = {}
    for bucket in data['aggregations']['subj_concept_counts']['buckets']:
        k = bucket['key']
        v = bucket['doc_count']
        if k in concept_counts:
            concept_counts[k] = concept_counts[k] + v
        else:
            concept_counts[k] = v

    most_occuring_concept = max(concept_counts, key=concept_counts.get)
    return most_occuring_concept


def _get_statement_ids(factors, concept, index_id):
    es_client = es_service.get_client()
    data = es_client.search(
        index=index_id,
        size=10000,
        _source_includes=['id'],
        body={
            'query': {
                'bool': {
                    'should': [
                        {
                            'bool': {
                                'must': [
                                    {'terms': {'subj.factor': factors}},
                                    {'term': {'subj.concept': concept}}
                                ]
                            }
                        },
                        {
                            'bool': {
                                'must': [
                                    {'terms': {'obj.factor': factors}},
                                    {'term': {'obj.concept': concept}}
                                ]
                            }
                        }
                    ]
                }
            }
        }
    )

    return list(map(lambda x: x['_source']['id'], data['hits']['hits']))


def _get_factor(statement_id, concept, index_id):
    es_client = es_service.get_client()
    data = es_client.search(
        index=index_id,
        size=1,
        _source_includes=['subj', 'obj'],
        body={
            'query': {
                'term': {
                    'id': statement_id
                }
            }
        }
    )
    statement = data['hits']['hits'][0]['_source']
    if statement['subj']['concept'] == concept:
        return statement['subj']['factor']
    else:
        return statement['obj']['factor']


def _assert_recommendations_are_in_concept(concept, recommendations, index_id):
    factors = list(map(lambda x: x['factor'], recommendations))
    es_client = es_service.get_client()
    data = es_client.search(
        index=index_id,
        size=10000,
        _source_includes=['subj', 'obj'],
        body={
            'query': {
                'bool': {
                    'should': [
                        {
                            'bool': {
                                'must': [
                                    {'terms': {'subj.factor': factors, '_name': 'subj_factor'}},
                                    {'term': {'subj.concept': concept}}
                                ]
                            }
                        },
                        {
                            'bool': {
                                'must': [
                                    {'terms': {'obj.factor': factors, '_name': 'obj_factor'}},
                                    {'term': {'obj.concept': concept}}
                                ]
                            }
                        }
                    ]
                }
            }
        }
    )

    def _map_results(doc):
        if 'subj_factor' in doc['matched_queries'] and 'obj_factor' in doc['matched_queries']:
            return [doc['_source']['subj']['factor'], doc['_source']['obj']['factor']]
        elif 'subj_factor' in doc['matched_queries']:
            return [doc['_source']['subj']['factor']]
        else:
            return [doc['_source']['obj']['factor']]

    def reduce_results(accumulated_factors, factors):
        return accumulated_factors + factors

    assert set(list(reduce(reduce_results, list(map(_map_results, data['hits']['hits'])), []))) == set(factors)


def test_visible_graph_filtering(client):
    kb_index_id = os.getenv("TEST_KB_INDEX")  # "indra-cb126722-d748-11ea-a0bd-a45e60f1355d"
    project_index_id = os.getenv("TEST_PROJECT_INDEX")  # "project-f9c4b20b-180b-4a2f-9b8b-d6773129b6b2"
    factor_reco_index_id = es_recommendations_helper.get_factor_recommendation_index_id(kb_index_id)

    # For Factor Recommendations
    largest_cluster_id = _get_largest_cluster(factor_reco_index_id)
    factors_in_cluster = _get_all_factors_in_cluster(largest_cluster_id, factor_reco_index_id)
    frequent_concept_in_cluster = _get_most_occurring_concept_for_all_factors(factors_in_cluster, project_index_id)
    statement_ids = _get_statement_ids(factors_in_cluster, frequent_concept_in_cluster, project_index_id)

    factor_text_original = _get_factor(statement_ids[0], frequent_concept_in_cluster, project_index_id)

    payload = {
        'project_id': project_index_id,
        'kb_id': kb_index_id,
        'factor': factor_text_original,
        'num_recommendations': 10000,
        'statement_ids': statement_ids
    }
    recommendations = client.post('/recommendations/regrounding/',
                                  data=json.dumps(payload),
                                  follow_redirects=True,
                                  content_type='application/json').get_json()['recommendations']

    _assert_recommendations_are_in_concept(frequent_concept_in_cluster, recommendations, project_index_id)
