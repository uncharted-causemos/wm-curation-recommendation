from flask import current_app as app
from clusters import compute_ith_concept_cluster
import os
import json
import spacy
from spacy.lemmatizer import Lemmatizer
import yaml
import numpy as np
import pandas as pd
import re
from numpy import linalg as LA
import umap
import hdbscan

with app.app_context():
    ontology_file_path = os.path.join(
        app.root_path, 'data', 'wm_with_flattened_interventions_metadata.yml')
    statements_file_path = os.path.join(
        app.root_path, 'data', 'statements.json')
    evidence_file_path = os.path.join(app.root_path, 'data', 'evidence.json')
    spacy_file_path = os.path.join(
        app.root_path, 'data', 'en_core_web_lg-2.2.5', 'en_core_web_lg', 'en_core_web_lg-2.2.5')


def init():
    statements = init_statements()
    evidence = init_evidence()
    # TODO: Load the same world embeddings that Eidos is using
    nlp = init_word_embeddings()
    lemmatizer = Lemmatizer(nlp.vocab.lookups)

    print("Loading concepts...")
    concepts, examples = load_concepts_and_examples()
    ontology_spans = convert_concept_examples_and_names_to_embeddings(
        concepts, examples, nlp)
    concept_vecs = compute_concept_vecs(ontology_spans)
    print("Finished loading concepts.")

    print("Preparing dataframe...")
    factor_statement_df = init_factor_statement_df(statements, nlp, lemmatizer)

    factors = factor_statement_df['factor'].tolist()
    factor_vectors = vectorize(factors, nlp)
    factor_vectors_matrix = reshape_factor_vectors(factor_vectors)
    print("Finished preparing dataframe.")

    print("Computing umap...")
    mapper = compute_umapper(factor_vectors_matrix, concept_vecs)
    cv_map = compute_umap_concept_vectors(concept_vecs, mapper)
    compute_umap_factor_vectors(
        factor_statement_df, factor_vectors_matrix, mapper)
    print("Finished computing umap.")

    compute_clusters(factor_statement_df)

    return (factor_statement_df, mapper, cv_map, concepts, statements, evidence)


def compute_umapper(factor_vectors_matrix, concept_vecs):
    return umap.UMAP(n_components=2).fit(np.concatenate([factor_vectors_matrix, concept_vecs.T]))


def compute_umap_concept_vectors(concept_vecs, mapper):
    return mapper.transform(concept_vecs.T)


def compute_umap_factor_vectors(factor_statement_df, factor_vectors_matrix, mapper):
    print("Computing umap for factors... This might take a while")
    fv_2d_map = mapper.transform(factor_vectors_matrix)
    factor_statement_df['fv_2d_map_x'] = fv_2d_map[:, 0]
    factor_statement_df['fv_2d_map_y'] = fv_2d_map[:, 1]
    print("Finished computing umap for factors")


def compute_clusters(factor_statement_df):
    print("Computing clusters...")
    clusterer = hdbscan.HDBSCAN(min_cluster_size=20)

    for i in range(0, 243):
        compute_ith_concept_cluster(i, clusterer, factor_statement_df)

    print("Finished computing clusters.")

# Reshape


def reshape_factor_vectors(factor_vectors):
    # Normalize all subject vectors & shape as matrix
    factor_vectors_matrix = np.asmatrix(np.concatenate(
        factor_vectors).reshape((len(factor_vectors), 300)))
    factor_vectors_matrix = factor_vectors_matrix / \
        LA.norm(factor_vectors_matrix, axis=1)[:, None]
    factor_vectors_matrix = np.nan_to_num(factor_vectors_matrix)
    return factor_vectors_matrix

# Vectorize


def vectorize(factors, nlp):
    print("Vectorizing factors... This will take a while")
    factor_vectors = list(map(lambda x: nlp(x).vector, factors))
    print("Finished vectorizing factors")
    return factor_vectors

# Clean


def remove_special_chars(sentence):
    return re.sub('[^a-zA-Z]', " ", sentence)


def remove_multiple_spaces(sentence):
    return re.sub('\s+', ' ', sentence)


def trim(sentence):
    return sentence.strip()


def remove_stopwords(sentence, nlp):
    return " ".join([word for word in sentence.split(" ") if word not in nlp.Defaults.stop_words])


def lemmatize(sentence, lemmatizer):
    return " ".join([lemmatizer.lookup(word) for word in sentence.split(' ')])


def clean(sentence, nlp, lemmatizer):
    sentence = sentence.lower()
    sentence = remove_special_chars(sentence)
    sentence = remove_stopwords(sentence, nlp)
    sentence = remove_multiple_spaces(sentence)
    sentence = trim(sentence)
    sentence = lemmatize(sentence, lemmatizer)
    return sentence

# Initialize


def init_factor_statement_df(statements, nlp, lemmatizer):
    subj_statement_df = pd.DataFrame({
        'statements': list(map(lambda x: x['id'], statements)),
        'concept': list(map(lambda x: x['subj_concept_name'], statements)),
        'concept1': list(map(lambda x: x['subj_concept_candidates'][1]['name'] if len(x['subj_concept_candidates']) >= 2 else None, statements)),
        'concept2': list(map(lambda x: x['subj_concept_candidates'][2]['name'] if len(x['subj_concept_candidates']) >= 3 else None, statements)),
        'concept3': list(map(lambda x: x['subj_concept_candidates'][3]['name'] if len(x['subj_concept_candidates']) >= 4 else None, statements)),
        'concept4': list(map(lambda x: x['subj_concept_candidates'][4]['name'] if len(x['subj_concept_candidates']) >= 5 else None, statements)),
        'scores': list(map(lambda x: x['subj_concept_score'], statements)),
        'scores1': list(map(lambda x: x['subj_concept_candidates'][1]['score'] if len(x['subj_concept_candidates']) >= 2 else None, statements)),
        'scores2': list(map(lambda x: x['subj_concept_candidates'][2]['score'] if len(x['subj_concept_candidates']) >= 3 else None, statements)),
        'scores3': list(map(lambda x: x['subj_concept_candidates'][3]['score'] if len(x['subj_concept_candidates']) >= 4 else None, statements)),
        'scores4': list(map(lambda x: x['subj_concept_candidates'][4]['score'] if len(x['subj_concept_candidates']) >= 5 else None, statements)),
        'factor': list(map(lambda x: clean(x['subj'], nlp, lemmatizer), statements)),
        'original_factors': list(map(lambda x: x['subj'], statements)),
        'type': list(map(lambda x: 'subj', statements))
    })
    obj_statement_df = pd.DataFrame({
        'statements': list(map(lambda x: x['id'], statements)),
        'concept': list(map(lambda x: x['obj_concept_name'], statements)),
        'concept1': list(map(lambda x: x['obj_concept_candidates'][1]['name'] if len(x['obj_concept_candidates']) >= 2 else None, statements)),
        'concept2': list(map(lambda x: x['obj_concept_candidates'][2]['name'] if len(x['obj_concept_candidates']) >= 3 else None, statements)),
        'concept3': list(map(lambda x: x['obj_concept_candidates'][3]['name'] if len(x['obj_concept_candidates']) >= 4 else None, statements)),
        'concept4': list(map(lambda x: x['obj_concept_candidates'][4]['name'] if len(x['obj_concept_candidates']) >= 5 else None, statements)),
        'scores': list(map(lambda x: x['obj_concept_score'], statements)),
        'scores1': list(map(lambda x: x['obj_concept_candidates'][1]['score'] if len(x['obj_concept_candidates']) >= 2 else None, statements)),
        'scores2': list(map(lambda x: x['obj_concept_candidates'][2]['score'] if len(x['obj_concept_candidates']) >= 3 else None, statements)),
        'scores3': list(map(lambda x: x['obj_concept_candidates'][3]['score'] if len(x['obj_concept_candidates']) >= 4 else None, statements)),
        'scores4': list(map(lambda x: x['obj_concept_candidates'][4]['score'] if len(x['obj_concept_candidates']) >= 5 else None, statements)),
        'factor': list(map(lambda x: clean(x['obj'], nlp, lemmatizer), statements)),
        'original_factors': list(map(lambda x: x['obj'], statements)),
        'type': list(map(lambda x: 'obj', statements))
    })

    factor_statement_df = pd.concat(
        [subj_statement_df, obj_statement_df], ignore_index=True)
    factor_statement_df['concept_cat'] = factor_statement_df['concept'].astype(
        'category').cat.codes
    return factor_statement_df


def init_word_embeddings():
    print("Loading word embeddings")
    nlp = spacy.load(spacy_file_path)
    print("Finished loading word embeddings")
    return nlp


def init_statements():
    print("Loading statements...")
    with open(statements_file_path, 'r') as statements_file:
        statements = json.load(statements_file)
        print("Finished loading statements.")
        return statements


def init_evidence():
    print("Loading evidence...")
    with open(evidence_file_path, 'r') as evidence_file:
        evidence = json.load(evidence_file)
        print("Finished loading evidence.")
        return evidence


def compute_concept_vecs(ontology_spans):
    return np.asmatrix(np.hstack([(os.vector).reshape(-1, 1) for os in ontology_spans]))


def convert_concept_examples_and_names_to_embeddings(concepts, examples, nlp):
    ontology_names = list(
        map(lambda x: x[x.rfind('/') + 1:].replace('_', ' '), concepts))
    flattened_examples = list(map(lambda x: " ".join(x), examples))
    examples_and_names = []
    for i in range(0, len(concepts)):
        examples_and_names.append(
            ontology_names[i] + " " + flattened_examples[i])
    return list(map(lambda x: nlp(x), examples_and_names))


def load_concepts_and_examples():
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


def recursively_build_concepts(ontology, sofar, names, examples):
    for component in ontology:
        if 'OntologyNode' in component.keys():
            names.append(sofar + '/' + component['name'])
            examples.append(component['examples'])
            continue

        component_name = list(component.keys())[0]

        recursively_build_concepts(
            component[component_name], sofar + '/' + component_name, names, examples)
