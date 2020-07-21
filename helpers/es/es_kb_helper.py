from services import es_service
from functools import reduce


def search_by_text_and_polarity(subj_factor_text_originals, obj_factor_text_originals, subj_polarity, obj_polarity, index_name):
    es_client = es_service.get_client()

    def _map_source(statement_doc):
        return {
            'subj': statement_doc['_source']['subj']['factor'],
            'obj': statement_doc['_source']['obj']['factor']
        }

    data = es_client.search(
        index=index_name,
        size=10000,
        scroll='5m',
        _source_includes=['subj.factor', 'obj.factor'],
        body={
            'query': {
                'bool': {
                    'must': [
                        {'term': {'subj.polarity': subj_polarity}},
                        {'term': {'obj.polarity': obj_polarity}},
                        {'terms': {'subj.factor': subj_factor_text_originals}},
                        {'terms': {'obj.factor': obj_factor_text_originals}}
                    ]
                }
            }
        }
    )

    sid = data['_scroll_id']
    scroll_size = len(data['hits']['hits'])

    results = []
    while scroll_size > 0:
        results = results + list(map(_map_source, data['hits']['hits']))

        data = es_client.scroll(scroll_id=sid, scroll='2m')
        sid = data['_scroll_id']
        scroll_size = len(data['hits']['hits'])

    es_client.clear_scroll(scroll_id=sid)
    print('Finished fetching statements filtered by polarity.')
    return results


def get_concept_candidates(factor_text_originals, kb_index_name):
    es_client = es_service.get_client()

    data = es_client.search(
        index=kb_index_name,
        size=10000,
        scroll='5m',
        _source_includes=['subj.candidates', 'obj.candidates', 'subj.factor', 'obj.factor'],
        body={
            'query': {
                'bool': {
                    'should': [
                        {'terms': {'subj.factor': factor_text_originals, '_name': 'subj'}},
                        {'terms': {'obj.factor': factor_text_originals, '_name': 'obj'}}
                    ]
                }
            }
        }
    )

    sid = data['_scroll_id']
    scroll_size = len(data['hits']['hits'])

    results = []
    while scroll_size > 0:
        results = results + list(map(_map_factor_source_to_concept_candidate, data['hits']['hits']))

        data = es_client.scroll(scroll_id=sid, scroll='2m')
        sid = data['_scroll_id']
        scroll_size = len(data['hits']['hits'])

    es_client.clear_scroll(scroll_id=sid)
    print('Finished fetching concept candidates for list of factors')

    deduped_results = _dedupe_on_factor_text_original(results)
    return deduped_results


def get_concept_candidates_for_factor(factor_text_original, kb_index_name):
    es_client = es_service.get_client()

    def _reduce_candidates(factor_x, factor_y):
        if len(factor_x['candidates']) < len(factor_y['candidates']):
            return factor_y
        else:
            return factor_x

    data = es_client.search(
        index=kb_index_name,
        size=10000,
        scroll='5m',
        _source_includes=['subj.candidates', 'obj.candidates', 'subj.factor', 'obj.factor'],
        body={
            'query': {
                'bool': {
                    'should': [
                        {'terms': {'subj.factor': [factor_text_original], '_name': 'subj'}},
                        {'terms': {'obj.factor': [factor_text_original], '_name': 'obj'}}
                    ]
                }
            }
        }
    )

    results = list(map(_map_factor_source_to_concept_candidate, data['hits']['hits']))
    result = reduce(_reduce_candidates, results)
    print('Finished fetching concept candidates for factor.')
    return result


def _dedupe_on_factor_text_original(factors):
    uniq_factors = {}
    for i in range(len(factors) - 1, 0, -1):
        fto = factors[i]['factor_text_original']

        if fto not in uniq_factors:
            uniq_factors[fto] = factors[i]
            continue

        if len(factors[i]['candidates']) > len(uniq_factors[fto]['candidates']):
            uniq_factors[fto] = factors[i]

    return list(uniq_factors.values())


def _map_factor_source_to_concept_candidate(statement_doc):
    factor_candidates = None
    factor_text_original = None
    subj_candidates = statement_doc['_source']['subj']['candidates']
    obj_candidates = statement_doc['_source']['obj']['candidates']
    subj_text = statement_doc['_source']['subj']['factor']
    obj_text = statement_doc['_source']['obj']['factor']
    matched_queries = statement_doc['matched_queries']

    if len(matched_queries) == 1 and matched_queries[0] == 'subj':
        factor_candidates = subj_candidates
        factor_text_original = subj_text
    elif len(matched_queries) == 1 and matched_queries[0] == 'obj':
        factor_candidates = obj_candidates
        factor_text_original = obj_text
    elif len(matched_queries) == 2:
        if len(subj_candidates) > len(obj_candidates):
            factor_candidates = subj_candidates
            factor_text_original = subj_text
        else:
            factor_candidates = obj_candidates
            factor_text_original = obj_text
    else:
        # This should never hit
        raise AssertionError  # TODO: Fix

    return {
        'candidates': factor_candidates,
        'factor_text_original': factor_text_original
    }
