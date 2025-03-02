import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
import pytest
from fastapi.testclient import TestClient
from app.main import app
import base64

# Create a logger for the test
logger = logging.getLogger(__name__)

@pytest.fixture
def client():
    """
    Provides a TestClient instance for the FastAPI app.
    """
    return TestClient(app)

def test_analyze_image_logging_only(client):
    """
    Test the /analyze-image endpoint but only log the response.
    """
    # Load an image and convert it to base64
    image_path = "tests/test_images/person1.webp"
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")

    test_payload = {
        "provider": "openai",
        "image_base64": base64_image
    }

    response = client.post("/analyze-image", json=test_payload)
    logger.info(f"Response status code: {response.status_code}")
    logger.info(f"Response JSON: {response.json()}")
