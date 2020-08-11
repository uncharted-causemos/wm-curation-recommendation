from flask import Blueprint, jsonify

errors = Blueprint('errors', __name__)


@errors.app_errorhandler(Exception)
def handle_exception(error):
    message = [str(x) for x in error.args]
    status_code = error.code if hasattr(error, 'code') else 500
    response = {
        'error': {
            'type': error.__class__.__name__,
            'message': message or error.description
        }
    }

    return jsonify(response), status_code
