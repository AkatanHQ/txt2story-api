import logging
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.utils.logger import logger

@pytest.fixture
def client():
    """
    Provides a TestClient instance for the FastAPI app.
    """
    return TestClient(app)

def test_generate_story_text_logging_only(client):
    """
    Test the /generate-story-text endpoint but only log the response.
    """
    test_payload = {
        "user_id": 123,
        "scenario": "A thrilling space adventure",
        "language": "English",
        "number_of_pages": 3,
        "entities": [
            {
                "id": 1,
                "name": "Captain Zarg",
                "appearance": "Tall, wearing a futuristic space suit"
            }
        ]
    }

    response = client.post("/generate-story-text", json=test_payload)
    logger.info(f"Response status code: {response.status_code}")
    logger.info(f"Response JSON: {response.json()}")
