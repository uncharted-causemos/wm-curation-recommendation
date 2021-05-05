from numpy import linalg as LA
from lib.spacy_wrapper import SpacyWrapper


class SpacyEmbedder():
    @classmethod
    def vectorize(cls, sentence, normalize=True):
        sentence_vector = SpacyWrapper.nlp()(sentence).vector
        if normalize:
            norm = LA.norm(sentence_vector)
            if norm != 0.0:
                sentence_vector = sentence_vector / norm
        return sentence_vector
