import docker
import flask
import flask_socketio
from config import config

app             = flask.Flask(import_name=__name__)
docker_client   = docker.APIClient()
socketio        = flask_socketio.SocketIO()
users           = {}

def create_app():
    app.config.from_object(obj=config["development"])

    with app.app_context():
        from . import routes

        socketio.init_app(app=app)
        
        return app