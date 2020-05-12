# Run Ingest:
* Pull ES: `docker pull docker.uncharted.software/wm-iaas/populated_indra_and_geodata:0.0.1`
* Run ES: `docker run -d -p 9200:9200 docker.uncharted.software/wm-iaas/populated_indra_and_geodata:0.0.1`
* Download spacy models from [here](https://github.com/explosion/spacy-models/releases//tag/en_core_web_lg-2.2.5), unzip and put folder in `data/` directory
* Download the `wm_with_flattened_interventions_metadata.yml` [here](https://github.com/WorldModelers/Ontologies/blob/master/wm_with_flattened_interventions_metadata.yml) and place in the `data/` directory
* Create virtualenv: `virtualenv .venv`
* Enable virtualenv: `source .venv/bin/activate`
* Pip install: `pip install -r requirements.txt`
* Run `python ingest.py`

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

# Run Linting
You can run linting using: `flake8 --exclude .venv,.vscode,__pycache__,data .`

# Setup App (Outdated for now)

* Ensure there's a data folder in the root folder with two files: `evidence.json` and `statements.json` and `wm_with_flattened_interventions_metadata.yml`
  * To get `evidence.json` and `statements.json` use mongoexport: `mongoexport --uri="mongodb://10.65.18.52:27017/WM" --collection=dart-20200104-stmts-location --out=data/statements-20200104-stmts-location.json --jsonArray` 
  * Sometimes only certain evidence is relevant, so to prune use `-q` option like so: `mongoexport --uri="mongodb://10.65.18.52:27017/WM" --collection=evidence --out=data/evidence-20200104-stmts-location-from-mongodb.json --jsonArray -q='{"for_export": true}'`. 
  * Download spacy [here](https://github.com/explosion/spacy-models/releases/tag/en_core_web_lg-2.2.5). Extract to the `data/` folder.

* You can run it on the host like so:
  * Create virtualenv: `virtualenv .venv`
  * Enable virtualenv: `source .venv/bin/activate`
  * Pip install: `pip install -r requirements.txt`
  * `chmod +x start_app.sh`
  * `./start_app.sh`

* Or you can run it in a docker using:
  * Create a data volume `docker volume create --name wmcr-data-volume`
  * Mount the data volume to a dummy container: `docker container create --name dummy -v wmcr-data-volume:/root hello-world`
  * Cd into the `data` direction and copy the data folder into the volume: `docker cp -L data/ dummy:/root`
  * Remove the dummy container: `docker rm dummy`
  * Build the container: `docker build -t wmcr:latest .`
  * `docker run --name wmcr --mount source=wmcr-data-volume,target=/app/data/ -p 5000:5000 -it wmcr:latest`
  * To enter the docker container: `docker run -it --entrypoint=/bin/bash wmcr:latest -i`