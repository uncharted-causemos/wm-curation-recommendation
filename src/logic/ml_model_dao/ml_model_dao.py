from abc import ABCMeta, abstractmethod


class MLModelDAO(metaclass=ABCMeta):

    @classmethod
    @abstractmethod
    def save(cls, data, file_path):
        pass

    @classmethod
    @abstractmethod
    def load(cls, file_path):
        pass
