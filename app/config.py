# app/config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask configuration
    DEBUG = True
    TESTING = True
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-default-secret-key')
    
    # API Keys from .env
    STABILITY_KEY = os.getenv('STABILITY_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Other configurations can go here
