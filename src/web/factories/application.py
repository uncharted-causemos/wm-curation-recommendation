import copy

from flask import Flask, request

from web.controllers import index_api, recommendation_api
from web.errors import errors
from web.factories.configuration import Config


def create_application():
    """
    Basic application configuration
    :return: Flask App instance
    """
    app = Flask("__name__",)
    app.config.from_object(Config)
    
    # Logging after every request.
    @app.after_request
    def after_request(response):
        if not request.data:
            return response

        # Only print out response that have params
        # attached to them
        body = copy.deepcopy(request.get_json())
        print(f'Request body: {body}')

        return response

    app.register_blueprint(index_api)
    app.register_blueprint(recommendation_api, url_prefix='/recommendation')
    app.register_blueprint(errors)
    return app
