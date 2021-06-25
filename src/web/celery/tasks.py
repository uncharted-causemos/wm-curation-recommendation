from ingest.ingestor import Ingestor
from elastic.elastic import Elastic
from web.celery import celery

try:
    from flask import current_app as app
except ImportError as e:
    print(e)

# progress will update the state with a message


def progress(instance, state, message):
    instance.update_state(state=state, meta={'status': message})


@celery.task(bind=True, name="tasks.compute_recommendations")
def compute_recommendations(self, index, remove_factors, remove_statements, es_host, es_port):
    message, state = (
        'Creating Recommendations',
        'PROGRESS'
    )

    try:
        # Notify the user that the long running process has begun
        progress(self, state, message)

        # Ingest
        es = Elastic(es_host, es_port, timeout=60)
        ingestor = Ingestor(index, remove_factors, remove_statements, es)
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
