import os
from web.celery.config import configure
from web.application import create_application


# For running flask app locally outside of docker
def create_app():
    return create_application()


def run():
    app = create_application()
    configure(app)
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    app.run(host)


if __name__ == '__main__':
    run()
