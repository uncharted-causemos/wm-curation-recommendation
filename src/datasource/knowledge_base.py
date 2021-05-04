import spacy

from datasource.clean import clean
from datasource.vectorize import vectorize

from datasource.utils import dedupe_recommendations


# KnoweledgeBase class is responsible for initializing the knowledge base


class KnowledgeBase():
    _factors = dict()
    _statements = dict()
    _build_factor = None
    _build_statement = None

    @staticmethod
    def from_source(source, nlp):
        try:
            return KnowledgeBase(source, nlp)
        except Exception as e:
            raise e

    @staticmethod
    def _build_factor_recommendation(clean, vectorize):
        def _build_impl(factor):
            clean_factor = clean(factor)
            return {
                'vector_300_d': vectorize(clean_factor).tolist(),
                'text_cleaned': clean_factor,
                'text_original': factor,
            }
        return _build_impl

    @staticmethod
    def _build_statement_recommendation(clean, vectorize):
        def _build_impl(obj_factor, subj_factor):
            statement = '{0} {1}'.format(subj_factor, obj_factor)
            clean_statement = clean(statement)
            return {
                'vector_300_d': vectorize(clean_statement).tolist(),
                'text_cleaned': clean_statement,
                'text_original': statement,
                'subj_factor': subj_factor,
                'obj_factor': obj_factor
            }
        return _build_impl

    @staticmethod
    def _dedupe_recommendations(data, vector_field_name, text_field_name, attr):
        list_agg_fields = ['subj_factor', 'obj_factor'] if attr == 'statements' else []
        data = dedupe_recommendations(data, 'vector_300_d', 'text_cleaned', list_agg_fields)
        return data

    def __init__(self, source, nlp, *args, **kwargs):
        self.file_contents = source

        # Attempt to curry the clean method with the lemmatizer and
        # nlp vocabulary
        try:
            nlp = spacy.load(nlp)

            _clean = clean(nlp)
            _vectorize = vectorize(nlp)

            self._build_factor = self._build_factor_recommendation(
                _clean, _vectorize)
            self._build_statement = self._build_statement_recommendation(
                _clean, _vectorize)
        except Exception as e:
            raise e

        # Create the factors and the statements
        for statement in self.file_contents:
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

    def process(self, attr):
        def _process(data):
            # Dedupe the data
            data = self._dedupe_recommendations(data, 'vector_300_d', 'text_cleaned', attr)

            # TODO: make a HyperparameterConfig file that defines these
            # parameters
            data = self.compute_umap(data, 300, 20, 0.01, 15)
            data = self.compute_clusters(data, 20, 15, 8, 0.01)
            data = self.compute_umap(data, 20, 2, 0.01, 15)

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
