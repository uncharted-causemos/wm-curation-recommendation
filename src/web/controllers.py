import math
import statistics

from flask import Blueprint, jsonify, request
from flask import current_app as app

from services.polarity_recommendation import get_candidate as p_get_candidate
from services.polarity_recommendation import compute_knn as p_compute_knn

from services.regrounding_recommendation import get_candidate as r_get_candidate
from services.regrounding_recommendation import compute_knn as r_compute_knn
from services.regrounding_recommendation import compute_kl_divergence

from web import tasks
from web.extensions import celery

from werkzeug.exceptions import BadRequest


index_api = Blueprint('index_api', __name__)
recommendation_api = Blueprint('recommendation_api', __name__)


@index_api.route('/')
def index():
    return jsonify({})


@recommendation_api.route('/<knowledge_base_id>', methods=['POST'])
def recommendation(knowledge_base_id):
    # Get the params
    body = request.get_json()
    remove_factors = body and bool(body.get('remove_factors'))
    remove_statements = body and bool(body.get('remove_statements'))

    # Run the Long running ingestion
    task = tasks.compute_recommendations.delay(
        knowledge_base_id,
        app.config['NLP_FILE_PATH'],
        remove_factors,
        remove_statements
    )
    return jsonify({
        'task_id': task.id
    })


@recommendation_api.route('/task/<task_id>')
def recommendation_result(task_id):
    task = celery.AsyncResult(task_id)
    return jsonify(task.info)


@recommendation_api.route('/<project_id>/regrounding', methods=['POST'])
def recommendation_regrounding(project_id):
    # Get the params
    body = request.get_json()

    # Determine if the user has made a valid request
    num_recommendations = int(body['num_recommendations'])
    if num_recommendations > 10000:  # Max num recommendations allowed
        raise BadRequest(
            description="num_recommendations must not exceed 10,000.")

    # Get the remaining params from the request body
    knowledge_base_id = body['knowledge_base_id']
    factor = body['factor']
    statement_ids = body['statement_ids']

    recommended_factors = []

    # Calculate the regrounding recommendations
    factor = r_get_candidate(factor, knowledge_base_id)
    if factor['cluster_id'] != -1:
        num_knn_recommendations = math.ceil(num_recommendations / 2.0)
        num_kl_nn_recommendations = math.floor(num_recommendations / 2.0)

        knn = r_compute_knn(
            factor,
            statement_ids,
            num_knn_recommendations,
            project_id,
            knowledge_base_id
        )
        kl_nn = compute_kl_divergence(
            factor,
            statement_ids,
            num_kl_nn_recommendations,
            project_id,
            knowledge_base_id
        )

        # Merging helper
        def _create_factor_scores_mapping(knn_results, kl_nn_results):
            factor_scores_mapping = {}

            def _add_to_factor_scores_mapping(result):
                factor = result['factor']
                score = result['score']
                if factor in factor_scores_mapping:
                    factor_scores_mapping[factor].append(score)
                else:
                    factor_scores_mapping[factor] = [score]

            for result in knn_results:
                _add_to_factor_scores_mapping(result)

            for result in kl_nn_results:
                _add_to_factor_scores_mapping(result)

            return factor_scores_mapping

        # Merge knn and kl_nn
        factor_scores_mapping = _create_factor_scores_mapping(knn, kl_nn)

        for factor, scores in factor_scores_mapping.items():
            recommended_factors.append({
                'factor': factor,
                # This is to make sure that scores found using both heuristics have lower distance and so are higher rated
                'score': statistics.mean(scores) if len(scores) > 1 else scores[0] + 1
            })

    return jsonify({'recommendations': recommended_factors})


@recommendation_api.route('/<project_id>/polarity', methods=['POST'])
def recommendation_polarity(project_id):
    # Get the params
    body = request.get_json()

    # Determine if the user has made a valid request
    num_recommendations = int(body['num_recommendations'])
    if num_recommendations > 10000:  # Max num recommendations allowed
        raise BadRequest(
            description="num_recommendations must not exceed 10,000.")

    # Get the remaining params from the request body
    knowledge_base_id = body['knowledge_base_id']
    subj = body['subj_factor']
    obj = body['obj_factor']
    polarity = body['polarity']
    statement_ids = body['statement_ids']

    recommended_statements = []

    # Calculate the polarity rec
    statement = p_get_candidate(subj, obj, knowledge_base_id)
    if statement['cluster_id'] != -1:
        recommended_statements = p_compute_knn(
            statement,
            statement_ids,
            polarity,
            num_recommendations,
            project_id,
            knowledge_base_id
        )

    return jsonify({'recommendations': recommended_statements})