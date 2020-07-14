import numpy as np


def build_factor_vector_matrix(factor_vectors):
    factor_vector_matrix = np.array(list(map(lambda x: x['factor_vector'], factor_vectors)))
    print('Factor vectors shape is: {}'.format(factor_vector_matrix.shape))
    return factor_vector_matrix
