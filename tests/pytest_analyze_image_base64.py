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
def test_analyze_image_base64(payload):
    """
    Test case for /analyze-image-base64 endpoint.
    Ensures that a valid base64 image returns a proper response.
    """
    # Base64-encoded image (replace with actual base64 string if needed)
    image_path = "tests/test_images/person1.webp"

    with open(image_path, "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

    # Test payload
    test_payload = {
        "provider": "openai",
        "vision_model": "gpt-4o",
        "image_base64": image_base64
    }
    
    response = client.post("/analyze-image-base64", json=test_payload)

    # Validate response
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
    
    json_response = response.json()
    print("\n🔍 Response JSON:", response.json())

    # Check if the response contains "detailed_appearance"
    assert "detailed_appearance" in json_response, "Response does not contain 'detailed_appearance'"
    assert isinstance(json_response["detailed_appearance"], str), "detailed_appearance should be a string"

    print("✅ Test passed! Base64 image was analyzed successfully.")

