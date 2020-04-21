from flask import Flask
from flask import request, jsonify
import json
import hdbscan
from clusters import compute_ith_concept_cluster

app = Flask(__name__)

with app.app_context():
    from initializer import init
    from recommendations import get_recommendations

    factor_statement_df, mapper, cv_map, concepts, statements, evidence = init()


@app.route("/recommendations/regrounding", methods=['GET'])
def regrounding_recommendations():
    statement_id = request.args.get('statement_id')
    factor_type = request.args.get('type')
    new_concept = request.args.get('new_concept')
    statement_subspace = request.args.getlist('statement_subspace')

    recommendations = get_recommendations(
        statement_id, factor_type, new_concept, statement_subspace, statements, evidence, factor_statement_df)

    response = list(map(lambda x: {
                    'statement_id': x['statements'], 'type': x['type']}, recommendations.to_dict(orient='records')))

    return jsonify(response)


@app.route("/recommendation_decisions/regrounding", methods=['POST'])
def regrounding_recommendation_decisions():
    body = request.get_json()
    statement_id = body['statement_id']
    factor_type = body['type']
    new_concept = body['new_concept']
    recommendation_decisions = body['recommendation_decisions']

    for rd in recommendation_decisions:
        if rd['accepted']:
            is_same_statement = factor_statement_df['statements'] == rd['statement_id']
            is_same_type = factor_statement_df['type'] == rd['type']

            # TODO: Currently just setting the statements to a new concept. Will figure out how to compute new score later
            factor_statement_df.loc[is_same_statement &
                                    is_same_type, 'concept'] == new_concept

    current_concept_cat = factor_statement_df.loc[(factor_statement_df['statements'] == statement_id) & (
        factor_statement_df['type'] == factor_type), 'concept_cat'].values[0]
    new_concept_cat = factor_statement_df.loc[(
        factor_statement_df['concept'] == new_concept), 'concept_cat'].values[0]

    clusterer = hdbscan.HDBSCAN(min_cluster_size=20)
    compute_ith_concept_cluster(
        current_concept_cat, clusterer, factor_statement_df)
    compute_ith_concept_cluster(
        new_concept_cat, clusterer, factor_statement_df)

    return {}


@app.route("/clusters", methods=['GET'])
def clusters():
    concept = request.args.get('concept')
    statement_ids = request.args.getlist('statement_subspace')

    concept_filter = factor_statement_df['concept'] == concept
    statement_id_filter = factor_statement_df['statements'].isin(statement_ids)
    # TODO: Use to_dict
    factor_statement_json_string = factor_statement_df[concept_filter & statement_id_filter].to_json(
        orient='records')
    factor_statment_dict = json.loads(factor_statement_json_string)

    clusters = list(map(lambda x: {'statement_id': x['statements'], 'type': x['type'], 'cluster_label': x['cluster_labels'], 'coords': {
                    'x': str(x['fv_2d_map_x']), 'y': str(x['fv_2d_map_y'])}}, factor_statment_dict))

    response = {
        'concept': {
            'coords': {
                'x': str(cv_map[concepts.index('/' + concept)][0]),
                'y': str(cv_map[concepts.index('/' + concept)][1])
            }
        },
        'clusters': clusters
    }

    return jsonify(response)


@app.route("/recommendations/polarity", methods=['GET'])
def polarity_recommendations():
    return "Not implemented yet."


@app.route("/recommendation_decisions/polarity/", methods=['POST'])
def polarity_recommendation_decisions():
    return "Not implemented yet."


@app.route("/project/create", methods=['POST'])
def create_project():
    return "Not implemented yet."


@app.route("/project/create/status", methods=['GET'])
def project_creation_status():
    return "Not implemented yet."


@app.route("/project/delete", methods=['POST'])
def delete_project():
    return "Not implemented yet."
