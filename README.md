Currently only able to run the app in a docker image. Ingest is run manually. 

# General Prerequisites:

# Environment Setup
1. Download spacy models from [here](https://github.com/explosion/spacy-models/releases//tag/en_core_web_lg-2.2.5), unzip and put folder in `data/` directory
2. Download [wm_with_flattened_interventions_metadata.yml](https://github.com/WorldModelers/Ontologies/blob/master/wm_with_flattened_interventions_metadata.yml) and place in the `data/` directory
3. `python -m venv .venv`
4. `source .venv/bin/activate`
5. `pip install -r requirements.txt`

# Ingest:
1. Perform steps in `Environment Setup` section
2. Update/Create `.env` with appropriate values
   1. `CLUSTERING_DIM` should be set to 20 by default
   2. `TEST_*` fields can be ignored as they're not used in the ingest portion
3. `python ingestor/ingest.py`

# Run App:
1. Perform steps in `Environment Setup` section
2. `export FLASK_APP="app:create_app"`
3. `python -m flask run --host=0.0.0.0`

# Docker setup for App
To enter a docker container: `docker exec -it <container_id> bash`

Note: If trying to access local host ES point variables in `.env` to `host.docker.internal`

## Local (Non-Swarm):
2. Build the container: `docker build -f Dockerfile.local.flask -t wmcr-service-local:latest .`
3. Run the container: `docker run --name wmcr-service-local -d -p 5000:5000 -it wmcr-service-local:latest`

# Run Tests
1. Perform steps in `Environment Setup` section
2. `pytest -v`

# Run Linting
You can run linting using: `flake8 --exclude .venv,.vscode,__pycache__,data --ignore E501 .`