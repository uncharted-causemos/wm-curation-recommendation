from datasource.data_orchestrator import DataOrchestrator
from datasource.concepts.concepts_processor import ConceptsProcessor
from logic.embeddings.spacy_embedder import SpacyEmbedder
from logic.reduction.umap_reducer import UmapReducer
from logic.clustering.hdbscan_clusterer import HDBScanClusterer
from logic.ml_model_dao.ml_model_docker_volume_dao import MLModelDockerVolumeDAO

from elastic.elastic_indices import get_concept_index_id


class ConceptsOrchestrator(DataOrchestrator):
    UMAP_REDUCER_MODEL_NAME = 'umap-reducer'
    HDBSCAN_CLUSTERER_MODEL_NAME = 'hdbscan-clusterer'

    def __init__(self, data_source, es_host, kb_index, use_saved_reducer=False, use_saved_clusterer=False):
        self.data_source = data_source
        self.load_reducer = use_saved_reducer
        self.load_clusterer = use_saved_clusterer
        self.ml_model_dao = MLModelDockerVolumeDAO(es_host, kb_index)
        self.curation_index_id = get_concept_index_id(kb_index)

    def orchestrate(self):
        if self.load_reducer:
            reducer = self.load_model(self.UMAP_REDUCER_MODEL_NAME)
        else:
            reducer = UmapReducer(300, 2, 0.01, 15)

        if self.load_clusterer:
            clusterer = self.load_model(self.HDBSCAN_CLUSTERER_MODEL_NAME)
        else:
            clusterer = HDBScanClusterer(2, 15, 8, 0.01)

        embedder = SpacyEmbedder(normalize=True)

        processor = ConceptsProcessor(self.data_source, reducer, clusterer, embedder)

        data = processor.process()

        if not self.load_reducer:
            self.save_model(reducer, self.UMAP_REDUCER_MODEL_NAME)
        if not self.load_clusterer:
            self.save_model(clusterer, self.HDBSCAN_CLUSTERER_MODEL_NAME)

        return data

    def load_model(self, name):
        return self.ml_model_dao.load(name, self.curation_index_id)

    def save_model(self, data, model_name):
        self.ml_model_dao.save(data, model_name, self.curation_index_id)
