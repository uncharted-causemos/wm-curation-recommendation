from abc import ABCMeta, abstractmethod


class MLModelDAO(metaclass=ABCMeta):

    @abstractmethod
    def save(self, data, model_name, index_typ):
        pass

    @abstractmethod
    def load(self, model_name, index_typ):
        pass

    @classmethod
    @abstractmethod
    def list_kb_indices(cls, es_host):
        pass

    @classmethod
    @abstractmethod
    def delete_kb_models(cls, es_host, kb_index):
        pass

    @classmethod
    @abstractmethod
    def list_models(cls):
        pass
