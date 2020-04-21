import pandas as pd

def get_others_with_close_candidates(statement_id, factor_type, new_concept, score_threshold, factor_statement_df):
    selected_row = factor_statement_df[(factor_statement_df['statements'] == statement_id) & (factor_statement_df['type'] == factor_type)]
    
    if selected_row.shape[0] == 0:
        print("Unable to find record by statement_id & type in get_others_with_close_candidates")
        return selected_row
    
    # Find other candidates with second/third/fourth/fifth concepts same as new concept
    current_concept = selected_row['concept'].values[0]
    
    same_current_concept = factor_statement_df['concept'] == current_concept
    
    same_second_candidate = same_current_concept & (factor_statement_df['concept1'] == new_concept)
    same_third_candidate = same_current_concept & (factor_statement_df['concept2'] == new_concept)
    same_fourth_candidate = same_current_concept & (factor_statement_df['concept3'] == new_concept)
    same_fifth_candidate = same_current_concept & (factor_statement_df['concept4'] == new_concept)
    
    first_score_diff = factor_statement_df['scores'] - factor_statement_df['scores1']
    second_score_diff = factor_statement_df['scores'] - factor_statement_df['scores2']
    third_score_diff = factor_statement_df['scores'] - factor_statement_df['scores3']
    fourth_score_diff = factor_statement_df['scores'] - factor_statement_df['scores4']

    close_new_concepts1 = factor_statement_df[same_second_candidate & (first_score_diff < score_threshold)]
    close_new_concepts2 = factor_statement_df[same_third_candidate & (second_score_diff < score_threshold)]
    close_new_concepts3 = factor_statement_df[same_fourth_candidate & (third_score_diff < score_threshold)]
    close_new_concepts4 = factor_statement_df[same_fourth_candidate & (fourth_score_diff < score_threshold)]
    
    return pd.concat([close_new_concepts1, close_new_concepts2, close_new_concepts3, close_new_concepts4])
    
def get_doc_intersection_for_single_evidence_factors(statement_id, factor_type, statements, evidence, factor_statement_df):
    selected_row = factor_statement_df[(factor_statement_df['statements'] == statement_id) & (factor_statement_df['type'] == factor_type)]
    
    if selected_row.shape[0] == 0:
        print("Unable to find record by statement_id & type in get_doc_intersection_for_single_evidence_factors")
        return selected_row
    
    # Find same factors (i.e those factors that after removing stopwords are the same)
    is_same_factor = factor_statement_df['factor'] == selected_row['factor'].values[0]
    is_same_concept = factor_statement_df['concept'] == selected_row['concept'].values[0]
    same_factors = factor_statement_df[is_same_factor & is_same_concept]

    # Filter factors with 1 evidence ID, get their evidence
    statement_ids = same_factors['statements'].tolist()
    statements_with_one_evidence = list(filter(lambda x: x['id'] in statement_ids and x['num_evidences'] == 1, statements))
    statement_ids_with_one_evidence = list(map(lambda x: x['id'], statements_with_one_evidence))
    factor_evidence = list(filter(lambda x: x['indra_id'] in statement_ids_with_one_evidence, evidence))
    
    # Get document ids
    factor_document_ids = list(map(lambda x: x['indra_raw']['annotations']['provenance'][0]['document']['@id'], factor_evidence))
    
    # Find evidences with same document ids
    evidence_from_same_document = list(filter( lambda x: x['indra_raw']['annotations']['provenance'][0]['document']['@id'] in factor_document_ids, evidence))
    evidence_from_same_document_ids = list(map(lambda x: x['indra_id'], evidence_from_same_document))

    # Find statements with evidence from same document
    statements_with_same_evidence = list(filter(lambda x: x['id'] in evidence_from_same_document_ids and x['num_evidences'] == 1, statements))
    statements_with_same_evidence_ids = list(map(lambda x: x['id'], statements_with_same_evidence))
    
    return factor_statement_df[ (is_same_concept) & factor_statement_df['statements'].isin(statements_with_same_evidence_ids)]

def get_same_clusters(statement_id, factor_type, factor_statement_df):
    selected_row = factor_statement_df[(factor_statement_df['statements'] == statement_id) & (factor_statement_df['type'] == factor_type)]
    
    if selected_row.shape[0] == 0:
        print("Unable to find record by statement_id & type in get_same_clusters")
        return selected_row
    
    is_same_concept = factor_statement_df['concept'] == selected_row['concept'].values[0]
    is_same_cluster_id = factor_statement_df['cluster_labels'] == selected_row['cluster_labels'].values[0]
    
    if selected_row['cluster_labels'].values[0] == -1:
        return pd.DataFrame(columns = factor_statement_df.column_names)
    
    # Don't return if there's only one cluster (noise + one cluster)
    if len(factor_statement_df[is_same_concept]['cluster_labels'].unique()) <= 2:
        return pd.DataFrame(columns = factor_statement_df.column_names)

    return factor_statement_df[is_same_concept & is_same_cluster_id]

def get_recommendations(statement_id, factor_type, new_concept, statement_subspace, statements, evidence, factor_statement_df):
    #TODO: Dynamically select threshold here
    score_threshold = 0.02

    close_candidates = get_others_with_close_candidates(statement_id, factor_type, new_concept, score_threshold, factor_statement_df)
    same_doc = get_doc_intersection_for_single_evidence_factors(statement_id, factor_type, statements, evidence, factor_statement_df)
    clusters = get_same_clusters(statement_id, factor_type, factor_statement_df)

    recommendations = pd.concat([close_candidates, same_doc, clusters])
    
    #TODO: Should limit number of recommendations. Initially should be same_doc + clusters. If < 50 or 100, then add close_candidates to flesh it out
    return recommendations[recommendations['statements'].isin(statement_subspace)]