# Run Ingest:
* Pull ES: `docker pull docker.uncharted.software/wm-iaas/populated_indra_and_geodata:0.0.1`
* Run ES: `docker run -d -p 9200:9200 docker.uncharted.software/wm-iaas/populated_indra_and_geodata:0.0.1`
* Download spacy models from [here](https://github.com/explosion/spacy-models/releases//tag/en_core_web_lg-2.2.5), unzip and put folder in `data/` directory
* Download the `wm_with_flattened_interventions_metadata.yml` [here](https://github.com/WorldModelers/Ontologies/blob/master/wm_with_flattened_interventions_metadata.yml) and place in the `data/` directory
* Create virtualenv: `virtualenv .venv`
* Enable virtualenv: `source .venv/bin/activate`
* Copy `.env.example` to `.env`
* Pip install: `pip install -r requirements.txt`
* Run `python ingestor/ingest.py`

### Verify Ingest 
Make sure that a factor at random has the expected document structure

#### Concept Index:
```
curl -X GET "localhost:9200/curation_recommendation_concepts/_search?pretty" -H 'Content-Type: application/json' -d'
{
    "size": 1,
    "query": {
        "match_all": {}
    }
}
'
```

#### Factors Index:
```
curl -X GET "localhost:9200/curation_recommendation_kb_indra-48db558a-8fcb-11ea-9f42-acde48001122/_search?pretty" -H 'Content-Type: application/json' -d'
{
    "size": 1,
    "query": {
        "match_all": {}
    }
}
'
```

# Run App
* Ensure ingestion has finished
* Enable virtualenv: `source .venv/bin/activate`
* Copy `.env.example` to `.env`
* Pip install: `pip install -r requirements.txt`
* Run: `python -m flask run` in the root folder

# Run Linting
You can run linting using: `flake8 --exclude .venv,.vscode,__pycache__,data .`

# Ingestor Stats
Here are some stats on runtime based on processing 13K statements.

Two things pop out:
* Processing factors takes the longest time. Using ES's `parallel_bulk` api, `process_factors.py(process)` was reduced from 276 seconds to 180 seconds
* Computing umap takes a decently long time. The issue with UMAP will likely be more on the memory side. Will try and get memory stats soon. 

**Without `parallel_bulk`**
```
   Ordered by: cumulative time
   List reduced from 11466 to 30 due to restriction <30>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        2    0.096    0.048  372.493  186.247 ingest.py:1(<module>)
   2037/1    0.031    0.000  372.493  372.493 {built-in method builtins.exec}
      152    0.051    0.000  276.554    1.819 actions.py:275(bulk)
    77078    0.183    0.000  276.504    0.004 actions.py:171(streaming_bulk)
        1    0.051    0.051  234.324  234.324 process_factors.py:7(process)
      410    0.436    0.001  213.619    0.521 actions.py:66(_chunk_actions)
    27145    0.371    0.000  200.915    0.007 embedding_service.py:34(compute_normalized_vector)
    26904    0.069    0.000  200.867    0.007 process_factors.py:42(_process_statements_into_factors)
    26902    0.217    0.000  200.797    0.007 process_factors.py:49(_build_factor)
    27145    0.196    0.000  199.855    0.007 embedding_service.py:30(compute_vector)
    27145    4.929    0.000  198.350    0.007 language.py:414(__call__)
676925/108308    1.222    0.000  189.387    0.002 model.py:161(__call__)
   108308    1.249    0.000  151.477    0.001 model.py:130(predict)
406155/81231    2.604    0.000  137.059    0.002 feed_forward.py:43(begin_update)
    54154    0.379    0.000  113.555    0.002 api.py:293(begin_update)
      913    0.008    0.000   87.349    0.096 utils.py:69(_wrapped)
      913    0.061    0.000   87.309    0.096 transport.py:299(perform_request)
   297847    3.107    0.000   87.127    0.000 layernorm.py:60(begin_update)
        1    0.046    0.046   84.196   84.196 compute_and_update_umap.py:8(compute_and_update)
      913    0.021    0.000   82.627    0.091 http_urllib3.py:198(perform_request)
      913    0.026    0.000   82.436    0.090 connectionpool.py:494(urlopen)
     8525    0.031    0.000   78.026    0.009 socket.py:655(readinto)
     8525   77.977    0.009   77.977    0.009 {method 'recv_into' of '_socket.socket' objects}
      913    0.021    0.000   77.524    0.085 connectionpool.py:351(_make_request)
      913    0.007    0.000   73.687    0.081 client.py:1278(getresponse)
      913    0.015    0.000   73.658    0.081 client.py:296(begin)
      913    0.016    0.000   73.451    0.080 client.py:263(_read_status)
     3669    0.027    0.000   73.449    0.020 {method 'readline' of '_io.BufferedReader' objects}
    81231    1.550    0.000   68.961    0.001 api.py:370(uniqued_fwd)
   216616    0.911    0.000   65.484    0.000 resnet.py:28(begin_update)
```

**With `parallel_bulk`**
```
   Ordered by: cumulative time
   List reduced from 11555 to 30 due to restriction <30>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        2    0.096    0.048  317.483  158.742 ingest.py:1(<module>)
   2041/1    0.035    0.000  317.483  317.483 {built-in method builtins.exec}
        1    0.074    0.074  181.600  181.600 process_factors.py:8(process)
    26904    0.016    0.000  174.422    0.006 actions.py:322(parallel_bulk)
     2025  174.379    0.086  174.379    0.086 {method 'acquire' of '_thread.lock' objects}
       68    0.001    0.000  174.378    2.564 threading.py:270(wait)
       56    0.001    0.000  174.377    3.114 pool.py:845(next)
        1    0.039    0.039   80.543   80.543 compute_and_update_umap.py:8(compute_and_update)
      859    0.008    0.000   68.847    0.080 utils.py:69(_wrapped)
      859    0.058    0.000   68.816    0.080 transport.py:299(perform_request)
      859    0.018    0.000   64.066    0.075 http_urllib3.py:198(perform_request)
      859    0.024    0.000   63.903    0.074 connectionpool.py:494(urlopen)
     8186    0.032    0.000   63.189    0.008 socket.py:655(readinto)
     8186   63.138    0.008   63.138    0.008 {method 'recv_into' of '_socket.socket' objects}
      859    0.019    0.000   58.902    0.069 connectionpool.py:351(_make_request)
      859    0.006    0.000   58.719    0.068 client.py:1278(getresponse)
      859    0.014    0.000   58.693    0.068 client.py:296(begin)
      859    0.016    0.000   58.501    0.068 client.py:263(_read_status)
     3453    0.025    0.000   58.498    0.017 {method 'readline' of '_io.BufferedReader' objects}
      150    0.037    0.000   48.837    0.326 actions.py:275(bulk)
    50174    0.050    0.000   48.800    0.001 actions.py:171(streaming_bulk)
        1    0.011    0.011   46.901   46.901 compute_and_update_umap.py:23(_compute)
    50228    0.032    0.000   44.460    0.001 actions.py:105(_process_bulk_chunk)
      204    0.004    0.000   44.416    0.218 __init__.py:410(bulk)
        1    0.022    0.022   37.509   37.509 compute_and_update_clusters.py:7(compute_and_update)
        1    0.023    0.023   32.200   32.200 dimension_reduction_service.py:4(fit)
        1    0.206    0.206   32.177   32.177 umap_.py:1588(fit)
        1    0.000    0.000   24.108   24.108 compute_and_update_umap.py:44(_update_factors)
      147    0.002    0.000   23.730    0.161 compute_and_update_clusters.py:23(_update)
  1531/22    0.004    0.000   22.438    1.020 compiler_lock.py:29(_acquire_compile_lock)
```

# Docker Setup (Outdated)
* Or you can run it in a docker using:
  * Create a data volume `docker volume create --name wmcr-data-volume`
  * Mount the data volume to a dummy container: `docker container create --name dummy -v wmcr-data-volume:/root hello-world`
  * Cd into the `data` direction and copy the data folder into the volume: `docker cp -L data/ dummy:/root`
  * Remove the dummy container: `docker rm dummy`
  * Build the container: `docker build -t wmcr:latest .`
  * `docker run --name wmcr --mount source=wmcr-data-volume,target=/app/data/ -p 5000:5000 -it wmcr:latest`
  * To enter the docker container: `docker run -it --entrypoint=/bin/bash wmcr:latest -i`