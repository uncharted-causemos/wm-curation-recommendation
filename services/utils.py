import numpy as np
import pandas as pd


def build_factor_vector_matrix(factor_vectors):
    factor_vector_matrix = np.array(list(map(lambda x: x['factor_vector'], factor_vectors)))
    print('Factor vectors shape is: {}'.format(factor_vector_matrix.shape))
    return factor_vector_matrix


def dedupe_factors(factors, text_field_name):
    # TODO: Maybe worth moving away from pandas here in the future
    factor_df = pd.DataFrame(factors)
    factor_df = factor_df[['id', 'factor_vector', text_field_name]]
    factor_df['id'] = factor_df['id'].apply(lambda x: [x])
    factor_df = factor_df.groupby(text_field_name).agg({
        'id': 'sum',
        'factor_vector': lambda x: x.iloc[0]
    })
    deduped_factors = factor_df.to_dict(orient='records')
    return deduped_factors
