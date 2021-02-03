from elastic.elastic_indices import get_factor_recommendation_index_id

from functools import reduce

from services.recommendation import get_recommendation_from_es
from services.utils import knn, kl_divergence

try:
    from flask import current_app as app
except ImportError as e:
    print(e)


def get_candidate(factor, index_name, es=None):
    factor_index_name = get_factor_recommendation_index_id(index_name)

    # Attempt to get the recommendation from es
    return get_recommendation_from_es(factor_index_name, factor, es=es)


def compute_knn(factor, num_recommendations, knowledge_base_index, es=None):
    factor_index_name = get_factor_recommendation_index_id(knowledge_base_index)

    def _map_knn_results(factor, score):
        return {
            'factor': factor['text_original'],
            'score': score
        }

    body = {
        'query': {
            'bool': {
                'filter': [
                    {'term': {'cluster_id': factor['cluster_id']}}
                ]
            }
        }
    }
    # FIXME: Once prod ES supports dense vectors.
    # Search for 10000 docs to then run knn on.
    # Limit to 10000 means it's possible that some or all of the actual k nearest neighbors are not returned (unlikely on smaller knowledge bases)
    # ES supports Dense Vectors and an internal knn algorithm, so we don't have to be limited by this. However, our production ES instance
    # doesn't support dense vectors, so this should be updated eventually.
    response = (es or app.config['ES']).search(factor_index_name, body, size=10000)

    # Compute knn using the generalized knn method
    knn_factors, knn_scores = knn(
        factor,
        list(map(lambda x: x['_source'], response['hits']['hits'])),
        num_recommendations
    )
    return list(map(_map_knn_results, knn_factors, knn_scores))


def compute_kl_divergence(factor, num_recommendations, project_index, knowledge_base_index, es=None, clustering_dim=20):
    factor_index_name = get_factor_recommendation_index_id(knowledge_base_index)

    def _map_kl_nn_results(factor, score):
        return {
            'factor': factor['text_original'],
            'score': score
        }

    # Get all factors in the same cluster
    body = {
        'query': {
            'bool': {
                'filter': [
                    {'term': {'cluster_id': factor['cluster_id']}}
                ]
            }
        }
    }
    included_fields = ['text_original', 'text_cleaned', f'vector_{clustering_dim}_d']
    response = (es or app.config['ES']).search_with_scrolling(factor_index_name, body, '5m', _source_includes=included_fields)

    def _map_source(doc):
        vector_field_name = f'vector_{clustering_dim}_d'
        doc['vector'] = doc[vector_field_name]
        doc.pop(vector_field_name, None)
        return doc

    factors_in_cluster = list(map(_map_source, response))

    # Getting candidates for kl_divergence helper
    def _get_concept_candidates(text, index):
        if not isinstance(text, list):
            text = [text]

        def _map_factor_source_to_concept_candidate(doc):
            factor_candidates = None
            text_original = None
            source = doc['_source']
            subj_candidates = source['subj']['candidates']
            obj_candidates = source['obj']['candidates']
            subj_text = source['subj']['factor']
            obj_text = source['obj']['factor']
            matched_queries = doc['matched_queries']

            if len(matched_queries) == 1 and matched_queries[0] == 'subj':
                factor_candidates = subj_candidates
                text_original = subj_text
            elif len(matched_queries) == 1 and matched_queries[0] == 'obj':
                factor_candidates = obj_candidates
                text_original = obj_text
            else:  # len(matched_queries) == 2:
                if len(subj_candidates) > len(obj_candidates):
                    factor_candidates = subj_candidates
                    text_original = subj_text
                else:
                    factor_candidates = obj_candidates
                    text_original = obj_text

            return {
                'candidates': factor_candidates,
                'text_original': text_original
            }

        # Get the candidates
        body = {
            'query': {
                'bool': {
                    'should': [
                        {'terms': {'subj.factor': text, '_name': 'subj'}},
                        {'terms': {'obj.factor': text, '_name': 'obj'}}
                    ],
                    'minimum_should_match': 1
                }
            }
        }
        included_fields = ['subj.candidates', 'obj.candidates', 'subj.factor', 'obj.factor']
        response = (es or app.config['ES']).search_with_scrolling(index, body, '5m', source=True, _source_includes=included_fields)

        return list(map(_map_factor_source_to_concept_candidate, response))

    # Get the candidates from factors in the same cluster as our input factor
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

    factors = list(map(lambda x: x['text_original'], factors_in_cluster))
    concept_candidates = _get_concept_candidates(factors, project_index)
    concept_candidates = _dedupe_on_factor_text_original(concept_candidates)

    # Get the candidate from the factor we want to reground
    def _reduce_candidates(factor_x, factor_y):
        if len(factor_x['candidates']) < len(factor_y['candidates']):
            return factor_y
        else:
            return factor_x

    concept_candidate = _get_concept_candidates(factor['text_original'], project_index)
    concept_candidate = reduce(_reduce_candidates, concept_candidate)

    # Compute kl divergence using the generalized method
    kl_nn_factors, kl_nn_scores = kl_divergence(
        concept_candidate,
        concept_candidates + [concept_candidate],
        num_recommendations
    )
    return list(map(_map_kl_nn_results, kl_nn_factors, kl_nn_scores))
