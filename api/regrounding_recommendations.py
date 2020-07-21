import os
from flask import Blueprint, request, jsonify
import numpy as np
from sklearn.neighbors import KDTree
from scipy.stats import entropy
from services import embedding_service, es_service, ontology_service
from helpers.es import es_factors_helper, es_kb_helper
from helpers.api import recommendations_helper
from helpers import utils

regrounding_recommendations_api = Blueprint('regrounding_recommendations_api', __name__)


@regrounding_recommendations_api.route('/', methods=['POST'])
def get_recommendations():
    body = request.get_json()
    project_index_name = body['project_name']
    kb_index_name = body['kb_name']
    factor_text_original = body['factor']

    factor_doc = recommendations_helper.get_factor(factor_text_original, kb_index_name)
    # FIXME: This should check if cluster_id is -1 I think so that we don't recommend noise?
    factors_in_cluster = recommendations_helper.get_factors_in_cluster(factor_doc['cluster_id'], kb_index_name)

    knn = recommendations_helper.compute_knn(factor_doc, factors_in_cluster, num_nn=100)
    kl_nn = recommendations_helper.compute_kl_divergence(factor_doc, factors_in_cluster, kb_index_name, num_nn=100)

    recommended_factors = knn + kl_nn

    response = {
        'factor_recommendations': recommended_factors
    }

    return jsonify(response)

    # all_factors = es_factors_helper.get_all_factors(factor_index_name=es_service.get_factor_index_name(kb_index_name), source_fields=['factor_text_original'])
    # factor_length = list(map(lambda x: len(x['_source']['factor_text_original']), all_factors))

    # print(f"# of factors: {len(factor_length)}")
    # response = {
    #     'length': max(factor_length)
    # }

    # return jsonify(response)
