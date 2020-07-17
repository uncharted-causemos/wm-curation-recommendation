import os
from services import es_service


def get_concept_candidates(factors, kb_index_name):
    es_client = es_service.get_client()
    all_factor_text_originals = list(map(lambda x: x['factor_text_original'], factors))

    def _map_source(statement_doc):
        factor_candidates = None
        factor_text_original = None
        subj_candidates = statement_doc['_source']['subj']['candidates']
        obj_candidates = statement_doc['_source']['obj']['candidates']
        subj_text = statement_doc['_source']['subj']['factor']
        obj_text = statement_doc['_source']['obj']['factor']
        matched_queries = statement_doc['matched_queries']

        if len(matched_queries) == 1 and matched_queries[0] == 'subj':
            factor_candidates = subj_candidates
            factor = subj_text
        elif len(matched_queries) == 1 and matched_queries[0] == 'obj':
            factor_candidates = obj_candidates
            factor = obj_text
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

    data = es_client.search(
        index=kb_index_name,
        size=10000,
        scroll='5m',
        _source_includes=['subj.candidates', 'obj.candidates', 'subj.factor', 'obj.factor'],
        body={
            'query': {
                'bool': {
                    'filter': [
                        {'terms': {'subj.factor': all_factor_text_originals, '_name': 'subj'}},
                        {'terms': {'obj.factor': all_factor_text_originals, '_name': 'obj'}}
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
    print(f'Finished fetching concept candidates for list of factors')
    return results
