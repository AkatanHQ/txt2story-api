from flask import Flask
from app.api import api

def create_app():
    # Specify the static folder during the Flask app initialization
    app = Flask(__name__, static_folder='../static', static_url_path='/static')

    # Register blueprints
    app.register_blueprint(api, url_prefix='/api')

    return app
