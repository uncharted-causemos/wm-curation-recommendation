import os
from pathlib import Path
from dotenv import load_dotenv
import sys

# Since the ingestor runs outside the scope of the app
# we need to add the root path of the app in order to have access to app packages
app_root_path = Path('.') / '../'
sys.path.insert(1, str(app_root_path.resolve()))

# Load env
env_path = Path('.') / '../.env'
load_dotenv(dotenv_path=env_path)

import services.elasticsearch_service as es_service

es_client = es_service.get_client()

data = es_client.search(
    index="curation_recommendation_kb_indra-48db558a-8fcb-11ea-9f42-acde48001122",
    size=100,
    body={
        "aggs": {
            "factors:": {
                "aggs": {
                    "top": {
                        "top_hits": {
                            "size": 100
                        }
                    }
                },
                "terms": {
                    "field": "factor_cleaned",
                    "size": 100
                }
            }
        },
        "query": {
            "match_all": {}
        },
        "size": 0
    }
)
