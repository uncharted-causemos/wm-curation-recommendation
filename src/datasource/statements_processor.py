from datasource.data_processor import DataProcessor
from logic.preprocessing.text_preprocessor import TextPreprocessor
from logic.embeddings.spacy_embedder import SpacyEmbedder
from logic.reduction.umap_reducer import UmapReducer
from logic.clustering.hdbscan_clusterer import HDBScanClusterer
from datasource.utils import dedupe_recommendations


class StatementsProcessor(DataProcessor):

    def __init__(self, source):
        self._statements = dict()

        self.source = source

        # TODO: make a HyperparameterConfig file that defines these
        # parameters
        self.reducerto20d = UmapReducer(300, 20, 0.01, 15)
        self.reducerto2d = UmapReducer(20, 2, 0.01, 15)
        self.clusterer = HDBScanClusterer(20, 15, 8, 0.01)
        self.embedder = SpacyEmbedder(normalize=True)

        # Create the statements
        for statement in self.source:
            obj_factor = statement['obj']['factor']
            subj_factor = statement['subj']['factor']

            state = self._build_statement(obj_factor, subj_factor)

            # Keep track of the unique statements
            if state['text_original'] not in self._statements:
                self._statements.update({state['text_original']: state})

    @property
    def statements(self):
        return list(self._statements.values())

    def process(self):
        data = self.statements

        data = self._dedupe_recommendations(data, 'vector_300_d', 'text_cleaned')

        data = self.reducerto20d.reduce(data)
        data = self.clusterer.cluster(data)
        data = self.reducerto2d.reduce(data)

        formatted_data = self._format_data(data)

        return formatted_data

    def _build_statement(self, obj_factor, subj_factor):
        statement = '{0} {1}'.format(subj_factor, obj_factor)
        clean_statement = TextPreprocessor.clean(statement)
        return {
            'vector_300_d': self.embedder.get_embedding(clean_statement).tolist(),
            'text_cleaned': clean_statement,
            'text_original': statement,
            'subj_factor': subj_factor,
            'obj_factor': obj_factor
        }

    def _dedupe_recommendations(self, data, vector_field_name, text_field_name):
        data = dedupe_recommendations(data, vector_field_name, text_field_name, ['subj_factor', 'obj_factor'])
        return data

    def _format_data(self, data):
        formatted_data = []
        for datum in data:
            for text, subj, obj in zip(datum['text_original'], datum['subj_factor'], datum['obj_factor']):
                copy = datum.copy()
                copy['text_original'] = text
                copy['subj_factor'] = subj
                copy['obj_factor'] = obj
                formatted_data.append(copy)
        return formatted_data
