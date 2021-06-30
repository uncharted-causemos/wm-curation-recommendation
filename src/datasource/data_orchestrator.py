from abc import ABCMeta, abstractmethod


class DataOrchestrator(metaclass=ABCMeta):

    @abstractmethod
    def orchestrate(self):
        pass
