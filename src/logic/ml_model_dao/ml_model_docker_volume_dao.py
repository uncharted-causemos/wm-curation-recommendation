import os
import shutil
import glob
from pathlib import PurePath
import pickle
import gzip
from logic.ml_model_dao.ml_model_dao import MLModelDAO
from web.configuration import Config


class MLModelDockerVolumeDAO(MLModelDAO):

    def __init__(self, es_host, kb_index):
        self.es_host = self._parse_host(es_host)
        self.kb_index = kb_index

    def save(self, data, model_name, curation_index):
        file_path = self._get_file_path(model_name, curation_index)

        directory = str(file_path.parent)

        if not os.path.exists(directory):
            os.makedirs(directory)

        file = gzip.GzipFile(file_path, 'wb')
        file.write(pickle.dumps(data))
        file.close()

    def load(self, model_name, curation_index):
        file_path = self._get_file_path(model_name, curation_index)
        file = gzip.GzipFile(file_path, 'rb')
        data = pickle.loads(file.read())
        file.close()
        return data

    def list_kb_indices(self):
        return os.listdir(PurePath(Config.ML_MODEL_DATA_DIR).joinpath(self.es_host))

    def delete_kb_models(self, kb_index):
        path = PurePath(Config.ML_MODEL_DATA_DIR).joinpath(self.es_host).joinpath(kb_index)
        try:
            shutil.rmtree(path)
        except Exception as e:
            print(f'Raised exception: {e}')

    @classmethod
    def list_models(cls):
        return [f for f in list(glob.iglob(str(PurePath(Config.ML_MODEL_DATA_DIR).joinpath('**/*')), recursive=True)) if os.path.isfile(f)]

    def _get_file_path(self, model_name, curation_index):
        return PurePath(Config.ML_MODEL_DATA_DIR).joinpath(self.es_host).joinpath(self.kb_index).joinpath(model_name).joinpath(curation_index)

    def _parse_host(self, es_host):
        # Even if the / is not found, we add 1 anyways, so it'll automatically be incremented
        ip_start_idx = es_host.rfind('/')
        return es_host[ip_start_idx + 1:]
