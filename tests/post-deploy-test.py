import argparse
import requests
import os
import sys

from pathlib import PurePath
sys.path.insert(1, str(PurePath(os.getenv('VIRTUAL_ENV') + '/../')))

from src.elastic.elastic import Elastic
from src.elastic.elastic_indices import get_factor_recommendation_index_id, get_statement_recommendation_index_id


def health_check(service_url):
    response = requests.get(service_url)
    r = response.json()
    assert r == {}


def get_project_index(es_url, es_port, index):
    es = Elastic(es_url, es_port)
    body = {
        "query": {
            "bool": {
                "filter": {
                    "term": {
                        "kb_id": index
                    }
                }
            }
        }
    }

    es_results = es.search('project', body, size=1)
    project_index = es_results['hits']['hits'][0]['_source']['id']
    return project_index


def regrounding(service_url, es_url, es_port, index, project_id):
    curation_index = get_factor_recommendation_index_id(index)
    es = Elastic(es_url, es_port)
    body = {
        "query": {
            "bool": {
                "must_not": {
                    "term": {
                        "cluster_id": -1
                    }
                }
            }
        }
    }
    es_results = es.search(curation_index, body, size=1)
    factor = es_results['hits']['hits'][0]['_source']['text_original']

    regrounding_endpoint = f'{service_url}/recommendation/{project_id}/regrounding'
    response = requests.post(regrounding_endpoint, json={
        'knowledge_base_id': index,
        'factor': factor,
        'num_recommendations': 10
    })
    r = response.json()
    assert 'recommendations' in r
    assert len(r['recommendations']) >= 1


def polarity(service_url, es_url, es_port, index, project_id):
    curation_index = get_statement_recommendation_index_id(index)
    es = Elastic(es_url, es_port)
    body = {
        "query": {
            "bool": {
                "must_not": {
                    "term": {
                        "cluster_id": -1
                    }
                }
            }
        }
    }
    es_results = es.search(curation_index, body, size=1)
    obj_factor = es_results['hits']['hits'][0]['_source']['obj_factor']
    subj_factor = es_results['hits']['hits'][0]['_source']['subj_factor']

    regrounding_endpoint = f'{service_url}/recommendation/{project_id}/polarity'
    response = requests.post(regrounding_endpoint, json={
        'knowledge_base_id': index,
        'subj_factor': subj_factor,
        'obj_factor': obj_factor,
        'num_recommendations': 10
    })
    r = response.json()
    assert 'recommendations' in r
    assert len(r['recommendations']) >= 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Post deployment script used to test basic functionality.')
    parser.add_argument('--s', type=str, nargs='?',
                        help='<host>:<port>. The host and port against which to run this test. Enter the publicly accessible IP address if applicable.')

    parser.add_argument('--e', type=str, nargs='?',
                        help='<host>:<port>. The Elasticsearch host and port against which to run this test. Enter the publicly accessible IP address if applicable.')

    parser.add_argument('--k', type=str, nargs='?',
                        help='The knowledge base index against which to run this test. Something like "indra-512...."')

    args = parser.parse_args()

    service_url = f'http://{args.s}'
    es_url = args.e.split(':')[0]
    es_port = args.e.split(':')[1]
    kb_index = args.k
    project_index = get_project_index(es_url, es_port, kb_index)

    health_check(service_url)
    regrounding(service_url, es_url, es_port, kb_index, project_index)
    polarity(service_url, es_url, es_port, kb_index, project_index)
    print('Tests succeeded')
