from abc import ABCMeta, abstractmethod


class Reducer(metaclass=ABCMeta):

    @abstractmethod
    def reduce(cls, data):
        pass
