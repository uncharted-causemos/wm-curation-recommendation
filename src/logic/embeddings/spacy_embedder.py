from numpy import linalg as LA
from lib.spacy_wrapper import SpacyWrapper
from logic.embeddings.embedder import Embedder

from spacy.lang.en.stop_words import STOP_WORDS


class SpacyEmbedder(Embedder):

    def __init__(self, normalize=True):
        self.normalize = normalize

    def get_embedding_matrix(self, sentences):
        raise NotImplementedError

    def get_embedding(self, sentence):
        sentence_vector = SpacyWrapper.embed(sentence).vector
        if self.normalize:
            norm = LA.norm(sentence_vector)
            if norm != 0.0:
                sentence_vector = sentence_vector / norm
        return sentence_vector
