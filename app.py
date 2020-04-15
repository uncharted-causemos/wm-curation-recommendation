from flask import Flask, flash, redirect, render_template, request, session, abort, send_from_directory
import faiss
import pandas as pd
import numpy as np
import spacy
import json
import yaml
import re
from scipy.stats import entropy
from numpy import linalg as LA
app = Flask(__name__)

@app.route("/")
def index():
    return send_from_directory('static', 'index.html')

@app.route("/get_factor_suggestions", methods=['GET'])
def get_factor_suggestions(query):
    return []

@app.route("/get_recommendations", methods=['GET'])
def get_recommendations():
    factor_to_recommend_on = clean(request.args.get("sq"))
    factor_ind = factors.index(factor_to_recommend_on)

    nn_df = find_vectors_near_factor_of_interest(factor_ind)
    nn_vecs, concept_vecs = reshape_nearest_neighbors_and_concept_vectors(nn_df)
    nn_concept_similarities = compute_cosine_sim_bw_nn_all_concepts(nn_vecs, concept_vecs)
    factor_concept_similarities = compute_cosine_sim_bw_factor_of_interest_all_concepts(factor_ind, concept_vecs)
    nn_df = compute_entropy(factor_ind, nn_df, factor_concept_similarities, nn_concept_similarities)
    nn_df = find_weak_groundings(nn_df, factor_statement_df)
    nn_df = get_concepts_and_original_factor(nn_df, factor_statement_df)
    nn_df = get_doc_intersection_for_nn(nn_df, factor_to_recommend_on, factor_statement_df)
    nn_df['total_score'] = nn_df['nn_scores'] + nn_df['entropy_scores']
    nn_df = nn_df.sort_values(by='total_score')
    return nn_df.to_json(orient='records', index=True)

# 8. 
def get_doc_intersection_for_nn(nn_df, factor_to_recommend_on, factor_statement_df):
    nn_df['doc_intersection'] = np.nan
    foi_doc_ids = get_doc_ids(factor_to_recommend_on, factor_statement_df)
    nn_df = nn_df.apply(get_doc_intersection, axis=1, args=[factor_statement_df, foi_doc_ids])
    return nn_df

def get_doc_ids(factor, factor_statement_df):
    statement_ids_of_interest = factor_statement_df.loc[factor_statement_df['factor'] == factor, 'statements'].tolist()[0]
    evidence_of_interest = filter(lambda x: x['indra_id'] in statement_ids_of_interest, evidence)

    provenance = list(map(lambda x: x['indra_raw']['annotations']['provenance'], evidence_of_interest))
    provenance = [item for sublist in provenance for item in sublist]
    provenance = list(map(lambda x: x['document']['@id'], provenance))
    
    return provenance

def get_doc_intersection(row, factor_statement_df, foi_doc_ids):
    document_ids = get_doc_ids(row['factor'], factor_statement_df)
    row['doc_intersection'] = set(document_ids).intersection(set(foi_doc_ids))
    return row

# 7.
def get_concepts_and_original_factor(nn_df, factor_statement_df):
    nn_df['concepts'] = np.nan
    nn_df['original_factors'] = np.nan

    return nn_df.apply(append_concepts_and_original_factor, axis=1, args=[factor_statement_df])

def append_concepts_and_original_factor(row, factor_statement_df):
    statement_ids_of_interest = factor_statement_df.loc[factor_statement_df['factor'] == row['factor'], 'statements'].tolist()[0]
    statements_of_interest = [s for s in statements if s['id'] in statement_ids_of_interest]
    
    row['concepts'] = set(factor_statement_df.loc[factor_statement_df['factor'] == row['factor'], 'concept'].tolist()[0])
    row['original_factors'] = set(factor_statement_df.loc[factor_statement_df['factor'] == row['factor'], 'original_factors'].tolist()[0])
    return row

# 6. 
def find_weak_groundings(nn_df, factor_statement_df):
    nn_df['has_weak_parent_score'] = np.nan
    nn_df['has_small_difference_score'] = np.nan
    return nn_df.apply(flag_weak_groundings, axis=1, args=[factor_statement_df])

def flag_weak_groundings(row, factor_statement_df):
    statement_ids = factor_statement_df[factor_statement_df['factor'] == row['factor']]['statements'].tolist()[0]
    factor_types = factor_statement_df[factor_statement_df['factor'] == row['factor']]['type'].tolist()[0]
    nn_statements = [s for s in statements if s['id'] in statement_ids]
    
    weak_score = False
    small_difference = False
    for s in nn_statements:
        if 'subj' in factor_types and s['subj_concept_score'] < 0.6 and weak_score == False:
            weak_score = True
        if 'subj' in factor_types and len(s['subj_concept_candidates']) >= 2 and abs(s['subj_concept_candidates'][0]['score'] - s['subj_concept_candidates'][1]['score']) < 0.05 and small_difference == False:
            small_difference = True
        
        if 'obj' in factor_types and s['obj_concept_score'] < 0.6 and weak_score == False:
            weak_score = True
        if 'obj' in factor_types and len(s['obj_concept_candidates']) >= 2 and abs(s['obj_concept_candidates'][0]['score'] - s['obj_concept_candidates'][1]['score']) < 0.05 and small_difference == False:
            small_difference = True
    
    row['has_weak_parent_score'] = weak_score
    row['has_small_difference_score'] = small_difference
    return row

# 5. 
def compute_entropy(factor_ind, nn_df, factor_concept_similarities, nn_concept_similarities):
    nn_df['entropy_scores'] = np.nan
    nn_df['factor'] = np.nan
    for i in range(0, 50):
        entropy_score = entropy(factor_concept_similarities, qk=np.asarray(nn_concept_similarities[i, :])[0])
        nn_ind = nn_df.loc[i, 'nn_indices']
        
        nn_df.loc[i, 'factor'] = factors[nn_ind]
        nn_df.loc[i, 'entropy_scores'] = max(0, entropy_score) # Ensure entropy is always positive (it's negative sometimes )
    return nn_df

# 4.
def compute_cosine_sim_bw_factor_of_interest_all_concepts(factor_ind, concept_vecs):
    fv = factor_vectors[factor_ind]
    fv_norm = LA.norm(fv)
    factor_concept_similarities = 1 - ( fv / fv_norm ).reshape(1, -1).dot(concept_vecs)
    factor_concept_similarities = np.asarray(factor_concept_similarities)[0]
    return factor_concept_similarities

# 3. 
def compute_cosine_sim_bw_nn_all_concepts(nn_vecs, concept_vecs):
    nn_concept_similarities = 1 - nn_vecs.dot(concept_vecs)
    return nn_concept_similarities

# 2. 
def reshape_nearest_neighbors_and_concept_vectors(nn_df):
    nn_vecs = factor_vectors_matrix[nn_df['nn_indices'].tolist(), :]
    concept_vecs = np.asmatrix(np.hstack([ ( os.vector / LA.norm(os.vector) ).reshape(-1, 1) for os in ontology_spans]))
    return (nn_vecs, concept_vecs)

# 1.
def find_vectors_near_factor_of_interest(factor_ind):
    (nn_scores, nn_indices) = factor_index.search(factor_vectors_matrix[factor_ind], 50)
    nn_scores = 1 - nn_scores[0]  # cosine similarity to distance
    nn_df = pd.DataFrame({'nn_scores': nn_scores, 'nn_indices': nn_indices[0]})
    nn_df.loc[:, 'nn_scores'] = nn_df['nn_scores'].apply(lambda x: max(0, x)) # Ensure cosine similarity is positive
    return nn_df


# Faiss cluster
def init_faiss():
    factor_index = faiss.IndexFlatIP(300)
    factor_index.add(factor_vectors_matrix)
    return factor_index

# Reshape
def reshape_factor_vectors():
    # Normalize all subject vectors & shape as matrix
    factor_vectors_matrix = np.asmatrix(np.concatenate(factor_vectors).reshape((len(factor_vectors), 300)))
    factor_vectors_matrix = factor_vectors_matrix / LA.norm(factor_vectors_matrix, axis=1)[:, None]
    return factor_vectors_matrix

# Vectorize
def vectorize():
    print("Vectorizing factors")
    factor_spacy = list(map(lambda x: nlp(x), factors))
    factor_vectors = list(map(lambda x: x.vector, factor_spacy))
    print("Finished vectorizing factors")
    return (factor_spacy, factor_vectors)


# Clean
def remove_special_chars(sentence):
    return re.sub('[^a-zA-Z]', " ", sentence)

def remove_multiple_spaces(sentence):
    return re.sub('\s+', ' ', sentence)

def remove_stopwords(sentence):
    return " ".join([word for word in sentence.split(" ") if word not in nlp.Defaults.stop_words])

def clean(sentence):
    sentence = sentence.lower()
    sentence = remove_special_chars(sentence)
    sentence = remove_multiple_spaces(sentence)
    sentence = remove_stopwords(sentence)
    return sentence

# Initialize
def init_factor_statement_df():
    subj_statement_df = pd.DataFrame({
        'statements': list(map(lambda x: [x['id']], statements)),
        'concept': list(map(lambda x: [x['subj_concept_name']], statements)),
        'factor': list(map(lambda x: clean(x['subj']), statements)),
        'original_factors': list(map(lambda x: [x['subj']], statements)),
        'type': list(map(lambda x: ['subj'], statements))
    })
    obj_statement_df = pd.DataFrame({
        'statements': list(map(lambda x: [x['id']], statements)),
        'concept': list(map(lambda x: [x['obj_concept_name']], statements)),
        'factor': list(map(lambda x: clean(x['obj']), statements)),
        'original_factors': list(map(lambda x: [x['obj']], statements)),
        'type': list(map(lambda x: ['obj'], statements))
    })
    
    subj_statement_df = subj_statement_df.loc[subj_statement_df['factor'] != '', :]
    obj_statement_df = obj_statement_df.loc[obj_statement_df['factor'] != '', :]
    factor_statement_df = pd.concat([subj_statement_df, obj_statement_df])
    factor_statement_df_deduped = factor_statement_df.groupby('factor', as_index=False).agg('sum')
    return factor_statement_df_deduped

def convert_concepts_to_embeddings():
    ontology_names = list(map(lambda x: x[x.rfind('/') + 1:], concepts))
    return list(map(lambda x: nlp(x.replace('_', ' ')), ontology_names))

def init_word_embeddings():
    print("Loading word embeddings")
    nlp = spacy.load("en_core_web_lg")
    print("Finished loading word embeddings")
    return nlp

def init_statements():
    with open("../data/statements.json", 'r') as statements_file:
        return json.load(statements_file)

def init_evidence():
    with open("../data/evidence.json", 'r') as evidence_file:
        return json.load(evidence_file)

def init_concepts():
    ontology_yml = None
    with open(ontology_file_path, 'r') as stream:
        try:
            ontology_yml = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    concepts = []
    examples = []
    recursively_build_concepts(ontology_yml, '', concepts, examples)
    return (concepts, examples)

# Accepts a yaml ontology
def recursively_build_concepts(ontology, sofar, names, examples):
    for component in ontology:
        if 'OntologyNode' in component.keys():
            names.append(sofar + '/' + component['name'])
            examples.append(component['examples'])
            continue

        
        component_name = list(component.keys())[0]

        recursively_build_concepts(component[component_name], sofar + '/' + component_name, names, examples)

ontology_file_path = '../data/wm_with_flattened_interventions_metadata.yml'
concepts = None
examples = None
statements = None
evidence = None
nlp = None
ontology_spans = None
factor_statement_df = None
factors = None
factor_spacy = None
factor_vectors = None
factor_index = None
factor_vectors_matrix = None

concepts, examples = init_concepts()
statements = init_statements()
evidence = init_evidence()
nlp = init_word_embeddings()
ontology_spans = convert_concepts_to_embeddings()

factor_statement_df = init_factor_statement_df()
factors = factor_statement_df['factor'].tolist()

factor_spacy, factor_vectors = vectorize()

factor_vectors_matrix = reshape_factor_vectors()
factor_index = init_faiss()
