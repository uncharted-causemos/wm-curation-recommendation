import os

from web.factories.application import create_application
from web.factories.celery import configure_celery


def create_app():
    return create_application()


def run():
    app = create_application()
    configure_celery(app)
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    app.run(host, debug=True)


if __name__ == '__main__':
    run()
