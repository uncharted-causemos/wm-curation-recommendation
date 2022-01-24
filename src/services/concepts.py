import numpy as np
from sklearn.neighbors import KDTree
from services.utils import get_all_concepts, get_concept_by_name


def find_similar_concepts(kb_id, concept_name, num_recommendations):
    es_concepts = get_all_concepts(kb_id)

    vectors = np.array(list(map(lambda x: x['vector_2_d'], es_concepts)))
    kd_tree = KDTree(vectors, metric='euclidean', leaf_size=100)

    concept = get_concept_by_name(kb_id, concept_name)

    nn_dist, nn_indices = kd_tree.query(
        np.array(concept['vector_2_d']).reshape(1, -1),
        k=num_recommendations
    )

    def _map_result(score_ind_tuple):
        score, ind = score_ind_tuple
        return{
            'concept': es_concepts[ind]['text_original'],
            'score': score
        }

    return list(map(_map_result, zip(nn_dist.reshape(-1).tolist()[1:], nn_indices.reshape(-1).tolist()[1:])))
