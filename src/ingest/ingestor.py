from datasource.factors_processor import FactorsProcessor
from datasource.statements_processor import StatementsProcessor

from elastic.elastic_indices import get_factor_recommendation_index_id, \
    get_statement_recommendation_index_id


_factor_mapping = {
    "dynamic": "strict",
    "properties": {
        "cluster_id": {
            "type": "integer"
        },
        "text_cleaned": {
            "type": "keyword"
        },
        "text_original": {
            "type": "keyword"
        },
        "vector_2_d": {
            "type": "float"
        }
    }
}

_statement_mapping = {
    "dynamic": "strict",
    "properties": {
        "cluster_id": {
            "type": "integer"
        },
        "obj_factor": {
            "type": "keyword"
        },
        "subj_factor": {
            "type": "keyword"
        },
        "text_cleaned": {
            "type": "keyword"
        },
        "text_original": {
            "type": "keyword"
        },
        "vector_2_d": {
            "type": "float"
        }
    }
}


class Ingestor():

    def __init__(self, index, remove_factors, remove_statements, es):
        self.index = index
        self.factor_index_name = get_factor_recommendation_index_id(self.index)
        self.statement_index_name = get_statement_recommendation_index_id(self.index)
        self.remove_factors = remove_factors
        self.remove_statements = remove_statements
        # TODO: Just pass ES in always
        self.es = es

    def ingest(self):
        self._set_up_indices()
        knowledge_base = self._fetch_knowledge_base()

        # Process the factors and statements
        for index_name, processor in [(self.factor_index_name, FactorsProcessor(knowledge_base)), (self.statement_index_name, StatementsProcessor(knowledge_base))]:
            data = processor.process()

            try:
                resp = self.es.bulk_write(index_name, data)
                print(f'Bulk write errors into {index_name} (if any): \n {resp}')
            except Exception as e:
                raise e

        self.es.refresh(self.factor_index_name)
        self.es.refresh(self.statement_index_name)

    def _set_up_indices(self):
        self._set_up_factor_index()
        self._set_up_statement_index()

    def _set_up_factor_index(self):
        if self.remove_factors:
            self.es.delete_index(self.factor_index_name)

        self.es.create_index(self.factor_index_name, _factor_mapping)

    def _set_up_statement_index(self):
        if self.remove_statements:
            self.es.delete_index(self.statement_index_name)

        self.es.create_index(self.statement_index_name, _statement_mapping)

    def _fetch_knowledge_base(self):
        body = {
            'query': {
                'match_all': {}
            }
        }
        statements = self.es.search_with_scrolling(
            self.index,
            body,
            scroll='1000m',
            size=10000,
            _source_includes=['obj.factor', 'subj.factor']
        )
        return list(statements)
