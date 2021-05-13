from logic.preprocessing.text_preprocessor import TextPreprocessor
from logic.embeddings.spacy_embedder import SpacyEmbedder
from logic.reduction.umap_reducer import UmapReducer
from logic.clustering.hdbscan_clusterer import HDBScanClusterer
from datasource.utils import dedupe_recommendations
from datasource.data_processor import DataProcessor


class FactorsProcessor(DataProcessor):

    def __init__(self, source):
        self._factors = dict()

        self.source = source

        # TODO: make a HyperparameterConfig file that defines these
        # parameters
        self.reducerto20d = UmapReducer(300, 20, 0.01, 15)
        self.reducerto2d = UmapReducer(20, 2, 0.01, 15)
        self.clusterer = HDBScanClusterer(20, 15, 8, 0.01)
        self.embedder = SpacyEmbedder(normalize=True)

        # Create the factors
        for statement in self.source:
            obj_factor = statement['obj']['factor']
            subj_factor = statement['subj']['factor']

            obj = self._build_factor(obj_factor)
            subj = self._build_factor(subj_factor)

            # Keep track of the unique factors
            for factor in [obj, subj]:
                if factor['text_original'] not in self._factors:
                    self._factors.update({factor['text_original']: factor})

    @property
    def factors(self):
        return list(self._factors.values())

    def process(self):
        # Dedupe the data
        data = self._dedupe_recommendations(self.factors, 'vector_300_d', 'text_cleaned')

        data = self.reducerto20d.reduce(data)
        data = self.clusterer.cluster(data)
        data = self.reducerto2d.reduce(data)

        formatted_data = self._format_data(data)

        return formatted_data

    def _build_factor(self, factor):
        clean_factor = TextPreprocessor.clean(factor)
        return {
            'vector_300_d': self.embedder.get_embedding(clean_factor).tolist(),
            'text_cleaned': clean_factor,
            'text_original': factor,
        }

    def _dedupe_recommendations(self, data, vector_field_name, text_field_name):
        data = dedupe_recommendations(data, vector_field_name, text_field_name, [])
        return data

    def _format_data(self, data):
        formatted_data = []
        for datum in data:
            for text in datum['text_original']:
                copy = datum.copy()
                copy['text_original'] = text
                formatted_data.append(copy)
        return formatted_data
