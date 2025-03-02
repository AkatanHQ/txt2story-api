import base64
import pytest
from fastapi.testclient import TestClient
from app.main import app
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Create test client for FastAPI
client = TestClient(app)

@pytest.mark.parametrize("payload", [{}])
def test_analyze_image_url(payload):
    """
    Test case for /analyze-image-url endpoint.
    Ensures that a valid image URL returns a proper response.
    """
    # Test payload
    test_payload = {
        "provider": "openai",
        "vision_model": "gpt-4o",
        "image_url": "https://vancouvergold.ca/wp-content/uploads/2013/11/person2-500x500.jpg"
    }
    
    response = client.post("/analyze-image-url", json=test_payload)

    # Validate response
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
    
    json_response = response.json()
    print("\n🔍 Response JSON:", response.json())

    # Check if the response contains "detailed_appearance"
    assert "detailed_appearance" in json_response, "Response does not contain 'detailed_appearance'"
    assert isinstance(json_response["detailed_appearance"], str), "detailed_appearance should be a string"

    print("✅ Test passed! Image URL was analyzed successfully.")
