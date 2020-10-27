from numpy import linalg as LA


# Vectorize the sentence
def vectorize(nlp):
    def _vectorize(sentence):
        sentence_vector = nlp(sentence).vector
        norm = LA.norm(sentence_vector)

        if norm != 0.0:
            sentence_vector = sentence_vector / norm
        return sentence_vector

    return _vectorize
