import os


class Config:
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
    CELERY_ACCEPT_CONTENT = ['json', 'yaml']
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_IMPORTS = ('web.tasks',)
