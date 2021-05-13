from abc import ABCMeta, abstractmethod


class DataProcessor(metaclass=ABCMeta):

    @abstractmethod
    def process(self):
        pass
