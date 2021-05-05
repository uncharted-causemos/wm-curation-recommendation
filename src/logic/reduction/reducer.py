from abc import ABCMeta, abstractmethod


class Reducer(metaclass=ABCMeta):

    @abstractmethod
    def reduce(cls, data):
        pass

    @abstractmethod
    def get_model_data(cls, data):
        pass
