import time

from logic.preprocessing.text_preprocessor import TextPreprocessor
from datasource.utils import dedupe_recommendations


class FactorsProcessor():

    def __init__(self, source, reducer, clusterer, embedder):
        self._factors = dict()

        self.source = source
        self.reducer = reducer
        self.clusterer = clusterer
        self.embedder = embedder

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
        print('Starting factor processing...')

        start_time = time.time()
        data = self._dedupe_recommendations(self.factors, 'vector_300_d', 'text_cleaned')
        print(f'Finished deduping. Took {time.time() - start_time}')

        start_time = time.time()
        data = self.reducer.reduce(data)
        print(f'Finished reducing. Took {time.time() - start_time}')

        start_time = time.time()
        data = self.clusterer.cluster(data)
        print(f'Finished clustering. Took {time.time() - start_time}')

        start_time = time.time()
        formatted_data = self._format_data(data)
        print(f'Finished factor processing. Took {time.time() - start_time}')

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
                del copy['vector_300_d']
                copy['text_original'] = text
                formatted_data.append(copy)
        return formatted_data
