Currently only able to run the app in a docker image. Ingest is run manually. 

# General Prerequisites:

# Environment Setup
1. Download spacy models from [here](https://github.com/explosion/spacy-models/releases//tag/en_core_web_lg-2.2.5), unzip and put folder in `data/` directory
2. `pip3 install -r requirements.txt` (create a virtualenv first if you so choose)
3. Fill in `ES_HOST`, `ES_PORT`, and `NLP_FILE_PATH` in the `.env` file with the appropriate settings

# Run App:
1. Perform steps in `Environment Setup` section (NB: If you wish to run the server locally you'll have to set `NLP_FILE_PATH` relative to `/src`)
2. There are 2 options depending on if you want to run locally or via docker.
    1. Run `docker-compose up --build` in the root of this project to run it via docker
    2. Run `docker build -t <image_name> .` and then `docker run -p 5000:5000 <image_name>` to run as a stand alone docker image. NOTE: If you're not running with docker swarm on our production environment, you'll need to modify the Dockerfile to include ES_HOST and ES_PORT.
    3. Run `export $(grep -v '^#' ../.env | xargs)` followed by `export FLASK_APP="src/app:create_app"`, and finally `python3 -m flask run --host=127.0.0.1` to run the server locally

# Run Ingestion (Locally):
1. `cd scripts`
2. `python3 ingestion.py -fs -i <indra_id> -u <es_url>`


# Docker setup for App
To enter a docker container: `docker exec -it <container_id> bash`

Note: If trying to access local host ES point variables in `.env` to `host.docker.internal`

# Run Linting
You can run linting using: `flake8 --exclude .venv,.vscode,__pycache__,data --ignore E501 .`
