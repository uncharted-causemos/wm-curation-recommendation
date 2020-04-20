from elasticsearch import Elasticsearch

class ElasticsearchService:
    client = None;

    def __init__(self):
        self.client = Elasticsearch(
            ['localhost'], #TODO LATER: change to read from .env
            http_auth=('', ''), #TODO LATER: add authentication
            scheme="https",
            port=443,
        )
    
