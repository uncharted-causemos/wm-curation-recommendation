from flask import Flask
from dotenv import load_dotenv, find_dotenv

# Load env before loading app specific files
load_dotenv(find_dotenv(), override=True)

from api.health_check import health_check_api
from api.regrounding_recommendations import regrounding_recommendations_api

app = Flask(__name__)

app.register_blueprint(health_check_api, url_prefix='/health_check')
app.register_blueprint(regrounding_recommendations_api, url_prefix='/recommendations/regrounding')
