import yaml
from dotenv import load_dotenv
import os

# Load .env file for sensitive environment variables
load_dotenv()

def load_config(config_file="config.yaml"):
    """Load configuration from YAML file."""
    try:
        with open(config_file, "r") as file:
            config = yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Configuration file {config_file} not found.")
        return {}
    except yaml.YAMLError as exc:
        print(f"Error parsing YAML file: {exc}")
        return {}

    return config

def get_env_variable(key, default_value=None):
    """Get an environment variable from .env file."""
    return os.getenv(key, default_value)
