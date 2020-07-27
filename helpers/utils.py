import numpy as np
import pandas as pd


def build_reco_vector_matrix(reco_vectors):
    reco_vector_matrix = np.array(list(map(lambda x: x['vector'], reco_vectors)))
    print('Recommendation vectors shape is: {}'.format(reco_vector_matrix.shape))
    return reco_vector_matrix


def dedupe_recommendations(recos, text_field_name):
    # TODO: Maybe worth moving away from pandas here in the future
    reco_df = pd.DataFrame(recos)
    reco_df = reco_df[['id', 'vector', text_field_name]]
    reco_df['id'] = reco_df['id'].apply(lambda x: [x])
    reco_df = reco_df.groupby(text_field_name).agg({
        'id': 'sum',
        'vector': lambda x: x.iloc[0]
    })
    deduped_recos = reco_df.to_dict(orient='records')
    return deduped_recos
