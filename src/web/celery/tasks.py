from services.recommendation import recommendations

from web.celery import celery


# progress will update the state with a message
def progress(instance, state, message):
    instance.update_state(state=state, meta={'status': message})


@celery.task(bind=True, name="tasks.compute_recommendations")
def compute_recommendations(self, index, remove_factors, remove_statements):
    message, state = (
        'Creating Recommendations',
        'PROGRESS'
    )

    try:
        # Notify the user that the long running process has begun
        progress(self, state, message)

        # Get the recommendations
        recommendations(index, remove_factors, remove_statements)

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
