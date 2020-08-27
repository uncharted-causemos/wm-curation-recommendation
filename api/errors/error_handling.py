import traceback
from flask import Blueprint, jsonify

errors = Blueprint('errors', __name__)


@errors.app_errorhandler(Exception)
def handle_exception(error):
    message = [str(x) for x in error.args]
    status_code = error.code if hasattr(error, 'code') else 500
    print(traceback.format_exc())
    response = {
        'error': {
            'type': error.__class__.__name__,
            'message': message,
            'description': error.description if hasattr(error, 'description') else ''
        }
    }
    print(f'The server threw an exception with message: {response}')
    return jsonify(response), status_code
