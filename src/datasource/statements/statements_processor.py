import time
import hashlib

from logic.preprocessing.text_preprocessor import TextPreprocessor
from datasource.utils import dedupe_recommendations


class StatementsProcessor():

    def __init__(self, source, reducer, clusterer, embedder):
        self._statements = dict()

        self.source = source
        self.reducer = reducer
        self.clusterer = clusterer
        self.embedder = embedder

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
        print('Starting statement processing...')

        start_time = time.time()
        data = self._dedupe_recommendations(self.statements, 'vector_300_d', 'text_cleaned')
        print(f'Finished deduping. Took {time.time() - start_time}')

        start_time = time.time()
        data = self.reducer.reduce(data)
        print(f'Finished reducing. Took {time.time() - start_time}')

        start_time = time.time()
        data = self.clusterer.cluster(data)
        print(f'Finished clustering. Took {time.time() - start_time}')

        start_time = time.time()
        formatted_data = self._format_data(data)
        print(f'Finished statement processing. Took {time.time() - start_time}')

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
                copy['_id'] = hashlib.sha256(text.encode('UTF-8')).hexdigest()
                del copy['vector_300_d']
                formatted_data.append(copy)
        return formatted_data
