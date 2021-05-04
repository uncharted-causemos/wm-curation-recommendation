from celery import Celery

from web.application import create_application
from web.celery.config import configure

celery: Celery = configure(create_application())
