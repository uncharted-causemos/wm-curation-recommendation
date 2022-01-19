import os
# Keeping this right at the top so env is loaded before anything else runs
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from elastic.elastic import Elastic


class Config:
    MODULE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    PROJECT_DIR = os.path.dirname(MODULE_DIR)

    default_scheme = 'http'
    if os.getenv('ES_USERNAME', '') != '':
        default_scheme = 'https'
    ES = Elastic(
        os.getenv('ES_HOST', ''),
        os.getenv('ES_PORT', '9200'),
        http_auth=(os.getenv('ES_USERNAME', ''), os.getenv('ES_PASSWORD', '')),
        scheme=os.getenv('ES_SCHEME', default_scheme)
    )

    DEBUG = True
    TESTING = True

    NLP_FILE_PATH = os.getenv('NLP_FILE_PATH')
    ML_MODEL_DATA_DIR = os.getenv('ML_MODEL_DATA_DIR')

    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', None)
    CELERY_RESULT_BACKEND = os.getenv('CELERY_BACKEND', None)
    CELERY_ACCEPT_CONTENT = ['json', 'yaml']
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_IMPORTS = ('web.celery.tasks',)
    CELERY_WORKER_HIJACK_ROOT_LOGGER = False
