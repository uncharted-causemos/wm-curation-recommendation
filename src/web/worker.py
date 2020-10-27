from celery import Celery

from web.factories.application import create_application
from web.factories.celery import configure_celery

celery: Celery = configure_celery(create_application())
