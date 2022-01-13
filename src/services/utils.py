try:
    from flask import current_app as app
except ImportError as e:
    print(e)

from elastic.elastic_indices import get_concept_index_id


def get_all_concepts(kb_id):
    # Create KD Tree of all Concepts
    body = {
        'query': {
            'match_all': {}
        }
    }
    es_results = app.config['ES'].search_with_scrolling(
        get_concept_index_id(kb_id),
        body,
        scroll='10m',
        size=10000)
    es_results = list(es_results)
    return es_results


def get_concept_by_name(kb_id, concept_name):
    body = {
        'query': {
            'bool': {
                'filter': {
                    'term': {
                        'text_original': concept_name
                    }
                }
            }
        }
    }
    es_results = app.config['ES'].search(
        get_concept_index_id(kb_id),
        body,
        size=1)
    es_results = list(map(lambda x: x['_source'], es_results['hits']['hits']))
    return es_results[0]


def get_recommendation_from_es(index, statement, es=None):
    # Create body
    body = {
        'query': {
            'bool': {
                'filter': [
                    {'term': {'text_original': statement}}
                ]
            }
        }
    }

    # Analyze response from es
    response = (es or app.config['ES']).search(index, body, size=1)
    hits = response['hits']['hits']
    if not hits:
        raise Exception(f'Unable to find Document with original_text {statement} in {index}')

    return hits[0]['_source']
