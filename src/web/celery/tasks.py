from ingest.ingestor import Ingestor
from elastic.elastic import Elastic
from web.celery import celery
from web.configuration import Config


def progress(instance, state, message):
    # progress will update the state with a message
    instance.update_state(state=state, meta={'status': message})


@celery.task(bind=True, name="tasks.compute_recommendations")
def compute_recommendations(self,
                            kb_index,
                            project_index,
                            statement_ids,
                            remove_factors,
                            remove_statements,
                            remove_concepts,
                            es_url):
    message, state = (
        'Creating Recommendations',
        'PROGRESS'
    )

    try:
        # Notify the user that the long running process has begun
        progress(self, state, message)

        # Ingest
        es = Elastic(es_url, http_auth=(Config.ES_USERNAME, Config.ES_PASSWORD), timeout=60)
        ingestor = Ingestor(
            es=es,
            kb_index=kb_index,
            project_index=project_index,
            statement_ids=statement_ids,
            remove_factors=remove_factors,
            remove_statements=remove_statements,
            remove_concepts=remove_concepts)
        ingestor.ingest()

        # Keep track of successful state
        message, state = (
            'Creation of Recommendations Succeeded for index',
            'SUCCESS'
        )
    except Exception as e:
        print(e)
        # Keep track of unsuccessful state
        state, message = (
            'Failed to Create Recommendations for index',
            'FAILURE'
        )
    finally:
        # Notify User of the state
        progress(self, state, message)

    return message
