from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object('app.config.Config')

    # Register Blueprints
    from app.api import api
    app.register_blueprint(api, url_prefix='/api')

    return app
