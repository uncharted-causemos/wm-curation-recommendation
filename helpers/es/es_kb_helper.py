from services import es_service
from functools import reduce


def get_concept_candidates_for_all_factors(text_originals, kb_index_id):
    results = _get_concept_candidates(text_originals, kb_index_id)
    results = list(map(_map_factor_source_to_concept_candidate, results))
    deduped_results = _dedupe_on_factor_text_original(results)
    return deduped_results


def get_concept_candidates_for_factor(text_original, kb_index_id):
    def _reduce_candidates(factor_x, factor_y):
        if len(factor_x['candidates']) < len(factor_y['candidates']):
            return factor_y
        else:
            return factor_x

    results = _get_concept_candidates([text_original], kb_index_id)
    results = list(map(_map_factor_source_to_concept_candidate, results))
    result = reduce(_reduce_candidates, results)
    print('Finished fetching concept candidates for factor.')
    return result


def _get_concept_candidates(text_originals, kb_index_id):
    es_client = es_service.get_client()

    data = es_client.search(
        index=kb_index_id,
        size=10000,
        scroll='5m',
        _source_includes=['subj.candidates', 'obj.candidates', 'subj.factor', 'obj.factor'],
        body={
            'query': {
                'bool': {
                    'should': [
                        {'terms': {'subj.factor': text_originals, '_name': 'subj'}},
                        {'terms': {'obj.factor': text_originals, '_name': 'obj'}}
                    ]
                }
            }
        }
    )

    sid = data['_scroll_id']
    scroll_size = len(data['hits']['hits'])

    results = []
    while scroll_size > 0:
        results = results + data['hits']['hits']

        data = es_client.scroll(scroll_id=sid, scroll='2m')
        sid = data['_scroll_id']
        scroll_size = len(data['hits']['hits'])

    es_client.clear_scroll(scroll_id=sid)
    print('Finished fetching concept candidates for list of factors')
    return results


def _dedupe_on_factor_text_original(factors):
    uniq_factors = {}
    for i in range(len(factors) - 1, 0, -1):
        fto = factors[i]['text_original']

        if fto not in uniq_factors:
            uniq_factors[fto] = factors[i]
            continue

        if len(factors[i]['candidates']) > len(uniq_factors[fto]['candidates']):
            uniq_factors[fto] = factors[i]

    return list(uniq_factors.values())


def _map_factor_source_to_concept_candidate(statement_doc):
    factor_candidates = None
    text_original = None
    subj_candidates = statement_doc['_source']['subj']['candidates']
    obj_candidates = statement_doc['_source']['obj']['candidates']
    subj_text = statement_doc['_source']['subj']['factor']
    obj_text = statement_doc['_source']['obj']['factor']
    matched_queries = statement_doc['matched_queries']

    if len(matched_queries) == 1 and matched_queries[0] == 'subj':
        factor_candidates = subj_candidates
        text_original = subj_text
    elif len(matched_queries) == 1 and matched_queries[0] == 'obj':
        factor_candidates = obj_candidates
        text_original = obj_text
    elif len(matched_queries) == 2:
        if len(subj_candidates) > len(obj_candidates):
            factor_candidates = subj_candidates
            text_original = subj_text
        else:
            factor_candidates = obj_candidates
            text_original = obj_text
    else:
        # This should never hit
        raise AssertionError  # TODO: Fix

    return {
        'candidates': factor_candidates,
        'text_original': text_original
    }
