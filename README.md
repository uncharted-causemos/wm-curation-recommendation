Currently only able to run the app in a docker image. Ingest is run manually. 

# General Prerequisites:

# Environment Setup
1. Download the large english spacy model from [here](https://spacy.io/models/en), unzip and put folder in `data/` directory
2. `pip3 install -r requirements.txt` (create a virtualenv first if you so choose)
3. Fill in `ES_HOST`, `ES_PORT`, and `NLP_FILE_PATH` in the `.env` file with the appropriate settings

# Run App:
1. Perform steps in `Environment Setup` section (NB: If you wish to run the server locally you'll have to set `NLP_FILE_PATH` relative to `/src`)
2. There are 2 options depending on if you want to run locally or via docker.
    1. Run `docker-compose up --build` in the root of this project to run it via docker
    2. Run `docker build -t <image_name> .` and then `docker run -p 5000:5000 --env-file ./.env <image_name>` to run as a stand alone docker image
    3. Run `export FLASK_APP="src/app:create_app"` followed by `python3 -m flask run --host=127.0.0.1` to run the server locally

# Run Ingestion (Locally):
1. `cd scripts`
2. `python3 ingestion.py -fs -i <indra_id> -u <es_url>`


# Docker setup for App
To enter a docker container: `docker exec -it <container_id> bash`

Note: If trying to access local host ES point variables in `.env` to `host.docker.internal`

After running `docker-compose` to quickly tear everything down, run `docker-compose down --rmi all --remove-orphans`

# Post Deployment Test

After activating the virtual environment, run `tests/post-deploy-test.py` script as follows:

`python post-deploy-test.py --s 10.64.18.99:5000 --e 10.64.18.99:9200 --k indra-4a2ad0cf-19e8-11eb-afec-fa163e9a8d5d `

Replace with your own parameters. 

# Using the ingestion service
To submit a new request

```
curl -H "Content-type:application/json" -XPOST http://<curation_server>:<port>/recommendation/ingest/<indra_index> -d'
{
  "remove_factors": true,
  "remove_statements": true,
  "es_host": <destination_es>,
  "es_port": 9200
}
'
```
Thisi will yield a `task_id`


To check the ingestion status
```
http://<curation_server>:<port>/recommendation/task/<task_id>
```

# Run Linting
You can run linting using: `flake8 --exclude .venv,.vscode,__pycache__,data --ignore E501 .`
