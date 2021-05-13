try:
    from flask import current_app as app
except ImportError as e:
    print(e)


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
