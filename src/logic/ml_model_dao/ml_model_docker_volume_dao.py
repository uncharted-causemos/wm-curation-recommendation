import os
import pickle
from logic.ml_model_dao.ml_model_dao import MLModelDAO


class MLModelDockerVolumeDAO(MLModelDAO):

    @classmethod
    def save(cls, data, file_path):
        directory = str(file_path.parent)

        if not os.path.exists(directory):
            os.makedirs(directory)

        pickle.dump(data, open(str(file_path), 'wb'))

    @classmethod
    def load(cls, file_path):
        return pickle.load(str(file_path))
