from flask import Flask
from app.api import api
from flask_cors import CORS

def create_app():
    # Specify the static folder during the Flask app initialization
    app = Flask(__name__, static_folder='../static', static_url_path='/static')

    # Enable CORS and allow specific origin (your frontend)
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

    # Register blueprints
    app.register_blueprint(api, url_prefix='/api')

    return app
