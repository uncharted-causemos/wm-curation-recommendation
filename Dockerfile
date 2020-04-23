FROM python:3.8-buster

WORKDIR /app

COPY app.py ./
COPY initializer.py ./
COPY recommendations.py ./
COPY clusters.py ./

COPY requirements.txt ./
COPY start_app.sh ./

COPY data/evidence.json ./data/evidence.json
COPY data/statements.json ./data/statements.json
COPY data/wm_with_flattened_interventions_metadata.yml ./data/wm_with_flattened_interventions_metadata.yml

RUN python -m pip install virtualenv
RUN python -m  virtualenv .venv
RUN ./.venv/bin/pip install -r requirements.txt
RUN ./.venv/bin/python -m spacy download en_core_web_lg

RUN chmod +x start_app.sh

ENV FLASK_APP app.py

EXPOSE 5000
ENTRYPOINT ["./start_app.sh"]