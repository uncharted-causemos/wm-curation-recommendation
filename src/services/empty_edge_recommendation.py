import numpy as np

try:
    from flask import current_app as app
except ImportError as e:
    print(e)

'''
This finds statements who have as candidates, the subj_concept and obj_concept in question.

Examples:
a) subj.candidate.score = 0.9 and obj.candidate.score = 0.1
b) subj.candidate.score = 0.4 and obj.candidate.score = 0.4
c) subj.candidate.score = 0.35 and obj.candidate.score = 0.9

There are three options for scoring edges:
1. average score: Take the average of subj.candidate.score and obj.candidate.score. But this ranks example (a) above example (b).
We want some sort of minimum standard for the candidates.

2. min score: Sort edges in descending order of min(subj.candidate.score, obj.candidate.score). This would rate example (b) above (a). 
But it would also rank it higher than example (c), whose minimum score is only slightly lower, but it's other score is much higher.

3. variable threshold: Here the goal is to find a variable threshold to serve as our minimum standard for candidates. Then rate the remaining 
edges based on their average score. The threshold is calculated as the mean(scores) - std(scores) i.e. slightly below the average of the scores of candidates
found for the subj_concept and obj_concept in question. 
'''


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
    edges_above_threshold = list(map(lambda x: {'id': x['id'], 'score': (
        x['subj_candidate']['score'] + x['obj_candidate']['score']) / 2}, edges_above_threshold))
    edges_above_threshold.sort(key=lambda x: x['score'])
    edges_above_threshold.reverse()

    return edges_above_threshold
