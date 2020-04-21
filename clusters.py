import numpy as np

def compute_ith_concept_cluster(i, clusterer, factor_statement_df):
    is_ith_concept = factor_statement_df['concept_cat'] == i
    concept_factors = factor_statement_df[is_ith_concept]
    factors_unique = concept_factors['factor'].drop_duplicates()
    
    fv_2d_unique_x = concept_factors.loc[factors_unique.index, 'fv_2d_map_x']
    fv_2d_unique_y = concept_factors.loc[factors_unique.index, 'fv_2d_map_y']
    fv_2d_unique = np.column_stack((fv_2d_unique_x, fv_2d_unique_y))
    
    if len(fv_2d_unique) <= 20:
        return
    
    cluster_labels = clusterer.fit_predict(fv_2d_unique)
    
    # TODO: There might be a smarter way to do this faster
    for index, factor in enumerate(factors_unique):
        factor_statement_df.loc[is_ith_concept & (factor_statement_df['factor'] == factor), 'cluster_labels'] =  cluster_labels[index]