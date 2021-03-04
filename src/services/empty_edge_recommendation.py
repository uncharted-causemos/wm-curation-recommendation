import numpy as np

try:
    from flask import current_app as app
except ImportError as e:
    print(e)


def get_edge_recommendations(project_id, subj_concept, obj_concept):
    body = {
        'query': {
            'bool': {
                'filter': [
                    {'term': {'subj.candidates.name': subj_concept}},
                    {'term': {'obj.candidates.name': obj_concept}}
                ]
            }
        }
    }
    response = app.config['ES'].search_with_scrolling(project_id,
                                                      body,
                                                      scroll='10m',
                                                      _source_includes=['id', 'subj.candidates', 'obj.candidates'],
                                                      size=10000)

    def _map_source(source):
        return {
            'id': source['id'],
            'subj_candidate': list(filter(lambda x: x['name'] == subj_concept, source['subj']['candidates']))[0],
            'obj_candidate': list(filter(lambda x: x['name'] == obj_concept, source['obj']['candidates']))[0]
        }

    edges = list(map(_map_source, response))
    scores = list(map(lambda x: x['subj_candidate']['score'], edges)) + list(map(lambda x: x['obj_candidate']['score'], edges))

    # TODO: If there are only two or three, what happens?
    score_mean = np.mean(scores)
    score_std = np.std(scores)
    score_threshold = score_mean - score_std

    print(f'Score mean: {score_mean}')
    print(f'Score standard deviation: {score_std}')
    print(f'Score threshold: {score_threshold}')

    edges_above_threshold = list(filter(lambda x: x['subj_candidate']['score'] > score_threshold and x['obj_candidate']['score'] > score_threshold, edges))
    edges_above_threshold.sort(key=lambda x: (x['subj_candidate']['score'] + x['obj_candidate']['score']) / 2)
    edges_above_threshold.reverse()

    return list(map(lambda x: x['id'], edges_above_threshold))
