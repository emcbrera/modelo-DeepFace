from flask import Flask
from flask_cors import CORS

from app.routes import api_v1


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(api_v1)

    return app


app = create_app()
