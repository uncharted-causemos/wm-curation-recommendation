from datasource.factors.factors_orchestrator import FactorsOrchestrator
from datasource.statements.statements_orchestrator import StatementsOrchestrator

from elastic.elastic_indices import get_factor_recommendation_index_id, \
    get_statement_recommendation_index_id
from logic.ml_model_dao.ml_model_docker_volume_dao import MLModelDockerVolumeDAO


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
    def __init__(self, es, kb_index, statement_ids, remove_factors, remove_statements):
        self.kb_index = kb_index
        self.factor_index_name = get_factor_recommendation_index_id(self.kb_index)
        self.statement_index_name = get_statement_recommendation_index_id(self.kb_index)
        self.remove_factors = remove_factors
        self.remove_statements = remove_statements
        self.es = es
        self.statement_ids = statement_ids
        self.is_delta_ingest = len(self.statement_ids) > 0

    def ingest(self):
        if self.is_delta_ingest:
            knowledge_base = self._fetch_knowledge_base(self.statement_ids)
        else:
            self._set_up_indices()
            knowledge_base = self._fetch_knowledge_base()

        # Process factors and statements
        orchestrators = [
            (
                self.factor_index_name,
                FactorsOrchestrator(
                    knowledge_base,
                    es_host=self.es.get_host(),
                    kb_index=self.kb_index,
                    use_saved_reducer=self.is_delta_ingest,
                    use_saved_clusterer=self.is_delta_ingest
                )
            ),
            (
                self.statement_index_name,
                StatementsOrchestrator(
                    knowledge_base,
                    es_host=self.es.get_host(),
                    kb_index=self.kb_index,
                    use_saved_reducer=self.is_delta_ingest,
                    use_saved_clusterer=self.is_delta_ingest
                )
            )
        ]
        # Process the factors and statements
        for index_name, orchestrator in orchestrators:
            data = orchestrator.orchestrate()

            resp = self.es.bulk_write(index_name, data)
            print(f'Bulk write errors into {index_name} (if any): \n {resp}')

        self._delete_stale_models()
        self.es.refresh(self.factor_index_name)
        self.es.refresh(self.statement_index_name)

    def _delete_stale_models(self):
        ml_model_dao = MLModelDockerVolumeDAO(self.es.get_host(), self.kb_index)
        indices = ml_model_dao.list_kb_indices()
        for index in indices:
            if self.es.index_exists(index) is False:
                ml_model_dao.delete_kb_models(index)
                print(f'Deleted models associated with index: {index}')

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

    def _fetch_knowledge_base(self, statement_ids=None):
        if statement_ids is None:
            body = {
                'query': {
                    'match_all': {}
                }
            }
        else:
            body = {
                'query': {
                    'bool': {
                        'filter': {
                            'terms': {
                                '_id': statement_ids
                            }
                        }
                    }
                }
            }
        statements = self.es.search_with_scrolling(
            self.kb_index,
            body,
            scroll='1000m',
            size=10000,
            _source_includes=['obj.factor', 'subj.factor']
        )
        return list(statements)
