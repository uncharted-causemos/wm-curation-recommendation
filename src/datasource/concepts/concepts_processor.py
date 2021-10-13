import time
import hashlib

from logic.preprocessing.text_preprocessor import TextPreprocessor
from logic.preprocessing.concept_text_preprocessor import ConceptTextPreProcessor
from datasource.utils import dedupe_recommendations


class ConceptsProcessor:

    def __init__(self, source, reducer, clusterer, embedder):
        self._concepts = dict()

        self.source = source
        self.reducer = reducer
        self.clusterer = clusterer
        self.embedder = embedder

        # Create the concepts

        for statement in self.source:
            obj = self._build_concept(statement['obj']['concept'])
            subj = self._build_concept(statement['subj']['concept'])

            # Keep track of the unique factors
            for concept in [obj, subj]:
                if concept['text_original'] not in self._concepts:
                    self._concepts.update({concept['text_original']: concept})

    @property
    def concepts(self):
        return list(self._concepts.values())

    def process(self):
        print('Starting concept processing...')

        start_time = time.time()
        data = self._dedupe_recommendations(self.concepts, 'vector_300_d', 'text_cleaned')
        print(f'Finished deduping. Took {time.time() - start_time}')

        start_time = time.time()
        data = self.reducer.reduce(data)
        print(f'Finished reducing. Took {time.time() - start_time}')

        start_time = time.time()
        data = self.clusterer.cluster(data)
        print(f'Finished clustering. Took {time.time() - start_time}')

        start_time = time.time()
        formatted_data = self._format_data(data)
        print(f'Finished concept processing. Took {time.time() - start_time}')

        return formatted_data

    def _build_concept(self, concept):
        cleaned_concept = TextPreprocessor.clean(ConceptTextPreProcessor.clean(concept))
        return {
            'vector_300_d': self.embedder.get_embedding(cleaned_concept).tolist(),
            'text_cleaned': cleaned_concept,
            'text_original': concept
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
                copy['_id'] = hashlib.sha256(text.encode('UTF-8')).hexdigest()
                formatted_data.append(copy)
        return formatted_data
