from abc import ABCMeta, abstractmethod


class Clusterer(metaclass=ABCMeta):

    @abstractmethod
    def cluster(cls, data):
        pass

    @abstractmethod
    def get_model_data(cls, data):
        pass
