from logic.preprocessing.text_preprocessor import TextPreprocessor
from logic.embeddings.spacy_embedder import SpacyEmbedder
from logic.reduction.umap_reducer import UmapReducer
from logic.clustering.hdbscan_clusterer import HDBScanClusterer
from datasource.utils import dedupe_recommendations


# KnoweledgeBase class is responsible for initializing the knowledge base


class KnowledgeBase():
    _factors = dict()
    _statements = dict()

    def __init__(self, source, *args, **kwargs):
        self.source = source
        self.reducer = UmapReducer()
        self.clusterer = HDBScanClusterer()

        # Create the factors and the statements
        for statement in self.source:
            obj_factor = statement['obj']['factor']
            subj_factor = statement['subj']['factor']

            obj = self._build_factor(obj_factor)
            subj = self._build_factor(subj_factor)
            state = self._build_statement(obj_factor, subj_factor)

            # Keep track of the unique factors and statements
            for factor in [obj, subj]:
                if factor['text_original'] not in self._factors:
                    self._factors.update({factor['text_original']: factor})

            if state['text_original'] not in self._statements:
                self._statements.update({state['text_original']: state})

    @property
    def factors(self):
        return list(self._factors.values())

    @property
    def statements(self):
        return list(self._statements.values())

    def _build_factor(self, factor):
        clean_factor = TextPreprocessor.clean(factor)
        return {
            'vector_300_d': SpacyEmbedder.vectorize(clean_factor).tolist(),
            'text_cleaned': clean_factor,
            'text_original': factor,
        }

    def _build_statement(self, obj_factor, subj_factor):
        statement = '{0} {1}'.format(subj_factor, obj_factor)
        clean_statement = TextPreprocessor.clean(statement)
        return {
            'vector_300_d': SpacyEmbedder.vectorize(clean_statement).tolist(),
            'text_cleaned': clean_statement,
            'text_original': statement,
            'subj_factor': subj_factor,
            'obj_factor': obj_factor
        }

    def _dedupe_recommendations(self, data, vector_field_name, text_field_name, attr):
        list_agg_fields = ['subj_factor', 'obj_factor'] if attr == 'statements' else []
        data = dedupe_recommendations(data, vector_field_name, text_field_name, list_agg_fields)
        return data

    def process(self, attr):
        def _process(data):
            # Dedupe the data
            data = self._dedupe_recommendations(data, 'vector_300_d', 'text_cleaned', attr)

            # TODO: make a HyperparameterConfig file that defines these
            # parameters
            data = self.reducer.reduce(data, 300, 20, 0.01, 15)
            data = self.clusterer.cluster(data, 20, 15, 8, 0.01)
            data = self.reducer.reduce(data, 20, 2, 0.01, 15)

            def _gen(data):
                for datum in data:
                    if attr == 'factors':
                        for text in datum['text_original']:
                            copy = datum.copy()
                            copy['text_original'] = text
                            yield copy
                    else:  # attr == 'statements'
                        for text, subj, obj in zip(datum['text_original'], datum['subj_factor'], datum['obj_factor']):
                            copy = datum.copy()
                            copy['text_original'] = text
                            copy['subj_factor'] = subj
                            copy['obj_factor'] = obj
                            yield copy

            return list(_gen(data))

        data = []
        try:
            data = self.__getattribute__(attr)
        except Exception as e:
            raise e

        return _process(data)
