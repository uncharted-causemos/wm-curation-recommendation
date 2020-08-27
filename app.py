from flask import Flask, request
from dotenv import load_dotenv, find_dotenv
import copy

# Load env before loading app specific files
load_dotenv(find_dotenv(), override=True)

from api.health_check import health_check_api
from api.regrounding_recommendations import regrounding_recommendations_api
from api.polarity_recommendations import polarity_recommendations_api
from api.errors.error_handling import errors


def create_app(testing=False):
    app = Flask("__name__", )
    app.config['TESTING'] = True

    @app.after_request
    def after_request(response):
        """ Logging after every request. """
        body = copy.deepcopy(request.get_json())
        del body['statement_ids']
        print(f'Request body: {body}')

        return response

    app.register_blueprint(health_check_api, url_prefix='/health_check')
    app.register_blueprint(regrounding_recommendations_api, url_prefix='/recommendations/regrounding')
    app.register_blueprint(polarity_recommendations_api, url_prefix='/recommendations/polarity')
    app.register_blueprint(errors)

    return app
