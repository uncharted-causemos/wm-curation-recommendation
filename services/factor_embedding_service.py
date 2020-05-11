import re
from spacy.lemmatizer import Lemmatizer
import spacy
import os
from numpy import linalg as LA

# TODO: Read in glove embeddings that Eidos uses


def _init_embeddings():
    global _nlp
    print("Reading in embeddings. This may take a while...")
    _nlp = spacy.load(os.getenv("embeddings_file_path"))
    print("Finished reading embeddings.")


def _init_lemmatizer():
    # TODO: Should I be lemmatizing given that Eidos doesn't?
    global _lemmatizer
    _lemmatizer = Lemmatizer(_nlp.vocab.lookups)


def _init_regex():
    global _regex_multiple_spaces
    global _regex_special_chars
    _regex_multiple_spaces = re.compile('\s+')
    _regex_special_chars = re.compile('[^a-zA-Z]')


def compute_vector(sentence):
    return _nlp(sentence).vector


def compute_normalized_vector(sentence):
    sentence_vector_300_d = compute_vector(sentence)
    norm = LA.norm(sentence_vector_300_d)

    if norm != 0.0:
        sentence_vector_300_d = sentence_vector_300_d / norm

    return sentence_vector_300_d


def clean(sentence):
    sentence = sentence.lower()
    sentence = _remove_special_chars(sentence)
    sentence = _remove_stopwords(sentence)
    sentence = _remove_multiple_spaces(sentence)
    sentence = _trim(sentence)
    sentence = _lemmatize(sentence)
    return sentence


def _remove_special_chars(sentence):
    return re.sub(_regex_special_chars, ' ', sentence)


def _remove_multiple_spaces(sentence):
    return re.sub(_regex_multiple_spaces, ' ', sentence)


def _trim(sentence):
    return sentence.strip()


def _remove_stopwords(sentence):
    return " ".join([word for word in sentence.split(" ") if word not in _nlp.Defaults.stop_words])


def _lemmatize(sentence):
    return " ".join([_lemmatizer.lookup(word) for word in sentence.split(' ')])


_init_embeddings()
_init_lemmatizer()
_init_regex()
