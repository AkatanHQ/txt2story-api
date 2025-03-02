import logging
import pytest
from fastapi.testclient import TestClient
from app.main import app

# Create a logger for the test
logger = logging.getLogger(__name__)

@pytest.fixture
def client():
    """
    Provides a TestClient instance for the FastAPI app.
    """
    return TestClient(app)

def test_generate_image_logging_only(client):
    """
    Test the /generate-image endpoint but only log the response.
    """
    test_payload = {
        "provider": "openai",  # or "azure"
        "image_prompt": "A futuristic spaceship among the stars",
        "entities": [
            {
                "id": 1,
                "name": "Captain Zarg",
                "appearance": "Tall, wearing a futuristic space suit"
            }
        ],
        "style": "COMIC",
        "image_model": "dall-e-3",
        "model_resolution": "1024x1024"
    }

    response = client.post("/generate-image", json=test_payload)
    logger.info(f"Response status code: {response.status_code}")
    logger.info(f"Response JSON: {response.json()}")
