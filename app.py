from flask import Flask
from dotenv import load_dotenv
import os

# Load env before loading app specific files
env_file_path = '.env'
load_dotenv(env_file_path, override=True)

from api.health_check import health_check_api
from api.regrounding_recommendations import regrounding_recommendations_api
from api.polarity_recommendations import polarity_recommendations_api
from api.errors.error_handling import errors


def create_app(testing=False):
    app = Flask("__name__", )
    app.config['TESTING'] = True

    app.register_blueprint(health_check_api, url_prefix='/health_check')
    app.register_blueprint(regrounding_recommendations_api, url_prefix='/recommendations/regrounding')
    app.register_blueprint(polarity_recommendations_api, url_prefix='/recommendations/polarity')
    app.register_blueprint(errors)

    return app
