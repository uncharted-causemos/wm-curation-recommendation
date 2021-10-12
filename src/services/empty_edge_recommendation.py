from re import sub
import numpy as np
from sklearn.neighbors import KDTree

try:
    from flask import current_app as app
except ImportError as e:
    print(e)

from src.elastic.elastic_indices import get_concept_index_id


def _get_all_concepts(kb_id):
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


def _get_concept_by_name(kb_id, concept_name):
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
        body)
    es_results = list(map(lambda x: x['_source'], es_results['hits']['hits']))
    return es_results[0]


def _get_edges(project_id, subj_concepts, obj_concepts):
    body = {
        'query': {
            'bool': {
                'must': [
                    {'terms': {'subj.concept.raw': subj_concepts}},
                    {'terms': {'obj.concept.raw': obj_concepts}}
                ]
            }
        }
    }

    nearest_edges = app.config['ES'].search_with_scrolling(
        project_id,
        body,
        scroll='10m',
        size=10000,
        _source_includes=['id', 'subj.concept', 'obj.concept'])
    nearest_edges = list(nearest_edges)
    return nearest_edges


'''
This finds the k nearest concepts in embedding space to both the subject and object concept of the empty edge.

Then it attempts to find edges in ES that are part of the bipartite graph formed by subject and object concepts. 

It scores the results from ES based on the distances in embedding space and returns that. 
'''


def get_edge_recommendations(kb_id, project_id, subj_concept, obj_concept):
    NUM_NEAREST_NEIGHBORS = 25

    es_concepts = _get_all_concepts(kb_id)

    vectors = np.array(list(map(lambda x: x['vector_2_d'], es_concepts)))
    kd_tree = KDTree(vectors, metric='euclidean', leaf_size=100)

    es_subj_concept = _get_concept_by_name(kb_id, subj_concept)
    es_obj_concept = _get_concept_by_name(kb_id, obj_concept)

    nn_dist_subj, nn_indices_subj = kd_tree.query(
        np.array(es_subj_concept['vector_2_d']).reshape(1, -1),
        k=NUM_NEAREST_NEIGHBORS
    )
    nn_dist_obj, nn_indices_obj = kd_tree.query(
        np.array(es_obj_concept['vector_2_d']).reshape(1, -1),
        k=NUM_NEAREST_NEIGHBORS
    )

    def _nearest_concepts(concept_indices):
        return [es_concepts[ind]['text_original'] for ind in concept_indices.reshape(-1)]

    def _create_concept_to_score_mapping(scores, concept_indices):
        return {es_concepts[concept_ind]['text_original']: scores.reshape(-1)[score_ind] for score_ind, concept_ind in enumerate(concept_indices.reshape(-1))}

    def _map_recommendation_with_score(subj_scores, obj_scores):
        def _map(recommendation):
            subj_concept = recommendation['subj']['concept']
            obj_concept = recommendation['obj']['concept']
            return {
                'id': recommendation['id'],
                'score': (subj_scores[subj_concept] + obj_scores[obj_concept]) / 2
            }
        return _map

    nearest_subj_concepts = _nearest_concepts(nn_indices_subj)
    nearest_obj_concepts = _nearest_concepts(nn_indices_obj)

    subj_scores = _create_concept_to_score_mapping(nn_dist_subj, nn_indices_subj)
    obj_scores = _create_concept_to_score_mapping(nn_dist_obj, nn_indices_obj)

    recommendations = _get_edges(project_id, nearest_subj_concepts, nearest_obj_concepts)

    return list(map(_map_recommendation_with_score(subj_scores, obj_scores), recommendations))
