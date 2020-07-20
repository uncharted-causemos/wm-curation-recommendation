import os
from flask import Blueprint, request, jsonify
import numpy as np
from sklearn.neighbors import KDTree
from scipy.stats import entropy
from services import embedding_service, es_service, ontology_service
from helpers.es import es_factors_helper, es_kb_helper
from helpers.api import recommendations_helper
from helpers import utils

polarity_recommendations_api = Blueprint('polarity_recommendations_api', __name__)


@polarity_recommendations_api.route('/', methods=['POST'])
def get_recommendations():
    body = request.get_json()
    project_index_name = body['project_name']
    kb_index_name = body['kb_name']
    subj_factor_polarity = body['subj']['polarity']
    obj_factor_polarity = body['obj']['polarity']
    subj_factor_text_original = body['subj']['factor']
    obj_factor_text_original = body['obj']['factor']
    subj_factor_text_cleaned = embedding_service.clean(subj_factor_text_original)
    obj_factor_text_cleaned = embedding_service.clean(obj_factor_text_original)

    subj_factor_doc = recommendations_helper.get_factor(subj_factor_text_original, kb_index_name)
    obj_factor_doc = recommendations_helper.get_factor(obj_factor_text_original, kb_index_name)
    # FIXME: This should check if cluster_id is -1 I think so that we don't load recommend more noise?
    factors_in_subj_cluster = recommendations_helper.get_factors_in_cluster(subj_factor_doc['cluster_id'], kb_index_name)
    factors_in_obj_cluster = recommendations_helper.get_factors_in_cluster(obj_factor_doc['cluster_id'], kb_index_name)

    # Get factors by text and polarity
    subj_factor_text_originals = list(map(lambda x: x['factor_text_original'], factors_in_subj_cluster))
    obj_factor_text_originals = list(map(lambda x: x['factor_text_original'], factors_in_obj_cluster))
    statements_in_same_clusters = es_kb_helper.search_by_text_and_polarity(
        subj_factor_text_originals,
        obj_factor_text_original,
        subj_factor_polarity,
        obj_factor_polarity,
        kb_index_name)  # TODO: Change this to use project_index_name

    subj_knn = recommendations_helper.compute_knn(factor_doc, factors_in_subj_cluster, num_nn=200)
    obj_knn = recommendations_helper.compute_knn(factor_doc, factors_in_obj_cluster, num_nn=200)
    subj_kl_nn = recommendations_helper.compute_kl_divergence(factor_doc, factors_in_subj_cluster, kb_index_name, num_nn=200)
    obj_kl_nn = recommendations_helper.compute_kl_divergence(factor_doc, factors_in_obj_cluster, kb_index_name, num_nn=200)

    recommended_factors = knn + kl_nn

    response = {
        'factor_recommendations': recommended_factors
    }

    return jsonify(response)


def _filter_factors_by_polarity(factors, polarity):
