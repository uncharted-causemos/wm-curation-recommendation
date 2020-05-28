from flask import Flask
from dotenv import load_dotenv, find_dotenv

# Load env before loading app specific files
load_dotenv(find_dotenv())

from api.health_check import health_check_api
from api.cluster_map import cluster_map_api
from api.project import project_api
from api.recommendation_decisions import recommendation_decisions_api
from api.recommendations import recommendations_api

app = Flask(__name__)

app.register_blueprint(health_check_api, url_prefix='/health_check')
app.register_blueprint(cluster_map_api, url_prefix='/cluster_map')
app.register_blueprint(project_api, url_prefix='/project')
app.register_blueprint(recommendation_decisions_api, url_prefix='/recommendation_decisions')
app.register_blueprint(recommendations_api, url_prefix='/recommendations')
