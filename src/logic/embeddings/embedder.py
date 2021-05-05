from abc import ABCMeta, abstractmethod


class Embedder(metaclass=ABCMeta):

    @abstractmethod
    def get_embedding_matrix(self, sentence):
        pass

    @abstractmethod
    def get_embedding(self, sentence):
        pass
