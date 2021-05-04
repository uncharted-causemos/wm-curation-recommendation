from celery import Celery

celery = Celery('celery_example', include=['web.celery.tasks'])
