from flask import Flask
from app.api import api

def create_app():
    app = Flask(__name__)
    
    # Configuration (if any)
    app.config.from_object('app.config.Config')  # If you have a config.py

    # Register blueprints
    app.register_blueprint(api, url_prefix='/api')
    
    return app
