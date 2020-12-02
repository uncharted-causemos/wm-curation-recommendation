from datasource.knowledge_base import KnowledgeBase

from elastic.elastic_indices import get_factor_recommendation_index_id, \
    get_statement_recommendation_index_id

try:
    from flask import current_app as app
except ImportError as e:
    print(e)

_factor_mapping = {
    "dynamic": "strict",
    "properties": {
        "cluster_id": {
            "type": "integer"
        },
        "text_cleaned": {
            "type": "keyword"
        },
        "text_original": {
            "type": "keyword"
        },
        "vector_20_d": {
            "type": "float"
        },
        "vector_2_d": {
            "type": "float"
        },
        "vector_300_d": {
            "type": "float"
        }
    }
}

_statement_mapping = {
    "dynamic": "strict",
    "properties": {
        "cluster_id": {
            "type": "integer"
        },
        "obj_factor": {
            "type": "keyword"
        },
        "subj_factor": {
            "type": "keyword"
        },
        "text_cleaned": {
            "type": "keyword"
        },
        "text_original": {
            "type": "keyword"
        },
        "vector_20_d": {
            "type": "float"
        },
        "vector_2_d": {
            "type": "float"
        },
        "vector_300_d": {
            "type": "float"
        }
    }
}


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


def recommendations(index, nlp, remove_factors, remove_statements, es=None):
    es = es or app.config['ES']

    # Remove the factor index
    factor_index_name = get_factor_recommendation_index_id(index)
    if remove_factors:
        es.delete_index(factor_index_name)

    # Create the new factor index
    _ = es.create_index(factor_index_name, _factor_mapping)

    # Remove the statement index
    statement_index_name = get_statement_recommendation_index_id(index)
    if remove_statements:
        es.delete_index(statement_index_name)

    # Create the new statement index
    _ = es.create_index(statement_index_name, _statement_mapping)

    # Get recommendations
    def _fetch_knowledge_base(es_client, index, nlp):
        # Create the KnowledgeBase from an ES scroll query
        body = {
            'query': {
                'match_all': {}
            }
        }
        statements = es_client.search_with_scrolling(index, body, '1000m', size=10000)
        return KnowledgeBase(statements, nlp)

    # Get the knowledge base
    knowledge_base = _fetch_knowledge_base(es, index, nlp)

    # Process the factors and statements
    for typ, index_name in [('factors', factor_index_name), ('statements', statement_index_name)]:
        data = knowledge_base.process(typ)

        try:
            resp = es.bulk_write(index_name, data)
            print(f'Bulk write errors into {index_name} (if any): \n {resp}')
        except Exception as e:
            raise e
    es.refresh(factor_index_name)
    es.refresh(statement_index_name)
