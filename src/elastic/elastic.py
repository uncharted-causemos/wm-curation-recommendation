from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


# Hardcoded configuration for now
es_bulk_config = {
    "chunk_size": 10000,
    "max_chunk_bytes": 5000000,
    "max_retries": 8,
    "initial_backoff": 3,
    "max_backoff": 300,
    "raise_on_error": False,
    "timeout": "60s"
}


# Establish an ES Client for use throughout the application
class Elastic:
    _host = None
    _port = None

    @staticmethod
    def client(host, **kwargs):
        """
        Return a new ES client
        """
        return Elastic(host, **kwargs)

    def __init__(self, host, **kwargs):
        """
        Initialize the ElasticSearch Client
        """
        self._host = host
        self.client = Elasticsearch(host, verify_certs=False, **kwargs)

    def get_host(self):
        return self._host

    def bulk_write(self, index, data):
        """
        Bulk write to ES
        """

        def _format_for_es(index, data):
            if not isinstance(data, list):
                data = [data]

            for datum in data:
                id = datum['_id']
                del datum['_id']
                yield {
                    '_id': id,
                    '_source': datum,
                    '_index': index
                }

        ok, response = bulk(self.client, _format_for_es(index, data), **es_bulk_config)

        if not ok:
            body = response[0]["index"]
            status = body["status"]

            # 400 range status signifies an error has ocurred
            if status in range(400, 500):
                error = body["error"]
                raise Exception("{} - {}".format(error["type"], error["reason"]))

        return response

    def search(self, index, body, **kwargs):
        """
        Query ES
        """
        return self.client.search(index=index, body=body, **kwargs)

    def search_with_scrolling(self, index, body, scroll, source=False, **kwargs):
        """
        Query ES with scrolling
        """
        search_response = self.search(index, body, scroll=scroll, **kwargs)

        # Get the Scroll ID from the response
        scroll_id = search_response['_scroll_id']

        # Yield the first set of hits
        hits = search_response['hits']['hits']
        if source:
            yield from hits
        else:
            yield from map(lambda x: x['_source'], hits)

        while hits:
            # Get the ES hits, and update the scroll_id
            scroll_id = search_response['_scroll_id']

            # Scroll forward, update the hits
            search_response = self.client.scroll(
                scroll_id=scroll_id,
                scroll=scroll
            )

            hits = search_response['hits']['hits']

            if source:
                yield from hits
            else:
                yield from map(lambda x: x['_source'], hits)

        # Clear the scroll
        self.client.clear_scroll(scroll_id=scroll_id)

    def index_exists(self, index):
        return self.client.indices.exists(index)

    def delete_index(self, index):
        """
        Delete an index in ES
        """
        response = {}
        if self.index_exists(index):
            response = self.client.indices.delete(index=index)
        return response

    def create_index(self, index, body={}):
        """
        Create an index in ES w/ or w/o a body
        """
        response = self.client.indices.create(
            index=index,
            body={'mappings': body}
        )
        return response

    def refresh(self, index):
        self.client.indices.refresh(index=index)
