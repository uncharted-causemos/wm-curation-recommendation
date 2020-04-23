FROM python:3.8-buster

WORKDIR /app

COPY app.py ./
COPY initializer.py ./
COPY recommendations.py ./
COPY clusters.py ./

COPY requirements.txt ./
COPY start_app.sh ./

RUN python -m pip install virtualenv
RUN python -m  virtualenv .venv
RUN ./.venv/bin/pip install -r requirements.txt

RUN chmod +x start_app.sh

ENV FLASK_APP app.py

EXPOSE 5000
ENTRYPOINT ["./start_app.sh"]