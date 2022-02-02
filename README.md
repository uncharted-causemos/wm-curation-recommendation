Currently only able to run the app in a docker image. Ingest is run manually. 

# General Prerequisites:

# Environment Setup
1. Download the large english spacy model from [here](https://spacy.io/models/en), by scrolling down to `en_core_web_lg`, click on release details which will take you to the github page, scroll down to assets and download the tar.gz file, unzip and put folder in `data/` directory
2. `pip3 install -r requirements.txt` (create a virtualenv first if you so choose)
3. Fill in `ES_URL`, and `NLP_FILE_PATH` in the `.env` file with the appropriate settings
4. In VSCode, if you want to debug ingestion locally, create a launch.json file (by going into the debugging panel on the left, and clicking "create a launch.json file"). Then paste the following into your launch.json file:
```
{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Ingestor",
            "type": "python",
            "request": "launch",
            "program": "ingestion.py",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}/scripts",
            "justMyCode": false,
            "args": [
                "-f",
                "-s",
                "-c",
                "-i",
                "indra-314b9db6-458c-4108-abdc-bdea07fe4cb2",
                "-u",
                "10.65.18.69:9200"
            ]
        }
    ]
}
```

# Run App:
1. Perform steps in `Environment Setup` section (NB: If you wish to run the server locally you'll have to set `NLP_FILE_PATH` relative to `/src`)
2. There are 3 options depending on if you want to run locally or via docker.
    1. Run `docker-compose up --build` in the root of this project to run it via docker
    2. Run `docker build -t <image_name> .` and then `docker run -p 5000:5000 --env-file ./.env <image_name>` to run as a stand alone docker image
    3. Run `export FLASK_APP="src/app:create_app"` followed by `python3 -m flask run --host=127.0.0.1` to run the server locally

# Run Ingestion (Locally):
1. `cd scripts`
2. `python3 ingestion.py -fs -i <indra_id> -u <es_url>`

# Run Ingestion/App (Dumpster Fire: 10.65.18.69):
1. Sync local code to dumpster-fire code because gitlab isn't accessible from dumpster-fire: `rsync -auv wm-curation-recommendation-service/ centos@10.65.18.69:~/wm-curation-recommendation --exclude=.venv/ --exclude=data/ --exclude=.git/ --exclude=.vscode/ --exclude=__pycache__/ --exclude=experiments/ --exclude=scripts/resources/ --exclude='**/*.pkl' --exclude='**/*.json'`. If `wm-curation-recommendation-service` is not the name of your folder containing the code, replace it with your root folder's name.
2. Ssh to dumpster fire and run app using instructions above
3. In order to run the app on the server such that it doesn't end when you close your ssh session, you need to run your commands in a tmux session. Run `tmux new -s curation-service`, then `tmux a -t curation-service`. This creates a session that will run even when you exit your ssh session. From within this tmux session, you can run the app using the instructions above. To exit: `ctrl + b, + d`
# Quick Docker Tips

`docker login docker-hub.uncharted.software`

To enter a docker container: `docker exec -it <container_id> bash`

Note: If trying to access local host ES point variables in `.env` to `host.docker.internal`

After running `docker-compose` to quickly tear everything down, run `docker-compose down --rmi all --remove-orphans`

# Post Deployment Test

After activating the virtual environment, run `tests/post-deploy-test.py` script as follows:

`python post-deploy-test.py --s 10.64.18.99:5000 --e 10.64.18.99:9200 --k indra-4a2ad0cf-19e8-11eb-afec-fa163e9a8d5d `

Replace with your own parameters. 


# Using the recommendation service
API requests asking for recommendations.

## Factor regrounding recommendation
Given a factor text, return statementIds and factors from the project that closely matches the provided factor in the embedding space.

```
POST /recommendation/:projectId/regrounding
{
  knowledge_base_id: xyz,
  factor: xyz,
  num_recommendations: 200
}
```


## Polarity recommendation
Given a set of factors, return statementIds from the project that closely matches the provided factors in the embedding space.

```
POST /recommendation/:projectId/polarity
{
  knowledge_base_id: xyz,
  subj_factor: abc,
  obj_factor: def,
  num_recommendations: 100
}
```


## Edge recommendation
Given subject and object concepts, return potential statements for regrounding
```
POST /recommendation/:projectId/edge-regrounding
{
  knowledge_base_id: xyz,
  subj_concept: abc,
  obj_concept: def,
  num_recommendations: 10
}
```


# Using the ingestion service
Request to agument the existing embedding space with new data. Ingestion service requires additional infrastructure to handle work and task management. Please see `docker-compose.yml` in the repository.

## To submit a new seed ingstion request for a new knowledge baase

```
curl -H "Content-type:application/json" -XPOST http://<curation_server>:<port>/recommendation/ingest/<indra_index> -d'
{
  "remove_factors": true,
  "remove_statements": true,
  "es_url": <destination_es>:9200
}
'
```
Thisi will yield a `task_id`


To check the ingestion status
```
http://<curation_server>:<port>/recommendation/task/<task_id>
```

## To submit an incremental ingestion request for project

```
curl -H "Content-type: application/json" -XPOST http:<curation_server>:<port>/recommendation/-delta-ingest/<indra_index> -d'
{
  "es_url": <destination_es>:9200,
  "statement_ids": [new statements from project],
  "project_id": <projectId>
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
