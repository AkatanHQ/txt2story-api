import os
import sys
import base64
import pytest
from fastapi.testclient import TestClient

# Make sure the project root is on the import path so that `app.main` resolves
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app  # noqa: E402

client = TestClient(app)


@pytest.mark.parametrize("payload", [{}])
def test_generate_image_with_reference_url(payload):
    """
    End-to-end test for `/generate-image` endpoint.

    Sends a prompt plus two entities (one carrying a reference image URL) to
    the endpoint and asserts that a valid base64-encoded image is returned.
    Then saves the image to a file for manual inspection.
    """

    test_payload = {
        "provider": "openai",
        "image_model": "gpt-image-1",
        "size": "1024x1024",
        "quality": "low",  # low/medium/high for GPT-Image-1
        "image_prompt": "A playful white kitten in an astronaut suit driving a six-wheeled rover across a crimson Martian dune under a pink sky",
        "entities": [
            {
                "name": "Luna",
                "appearance": "white Siamese kitten, blue eyes",
                "dreambooth_url": "https://i.pinimg.com/736x/b2/44/b4/b244b476322b182033bfa4ebbf69da7d.jpg"
            },
            {
                "name": "Astro Rover",
                "appearance": "compact six-wheeled rover with an orange chassis and solar-panel roof"
            }
        ]
    }

    response = client.post("/generate-image", json=test_payload)

    # Assert HTTP success
    assert response.status_code == 200, f"Unexpected status code: {response.status_code} — body: {response.text}"

    json_response = response.json()
    print("\n🖼️  Generate Image response keys:", json_response.keys())

    # Contract checks
    assert "image_b64" in json_response, "Response JSON should contain 'image_b64' field"
    b64_data = json_response["image_b64"]
    assert isinstance(b64_data, str), "'image_b64' must be a string"

    # Decode and save
    output_path = "generated_test_image.png"
    image_bytes = base64.b64decode(b64_data)
    with open(output_path, "wb") as f:
        f.write(image_bytes)

    print(f"✅ Image saved successfully: {output_path}")

    # Optionally open the image automatically (only works on local environments)
    try:
        from PIL import Image
        img = Image.open(output_path)
        img.show(title="Generated Test Image")  # This will open the image!
    except Exception as e:
        print(f"⚠️ Could not auto-open the image: {e}")

    print("✅ Test passed! Image was generated, saved, and displayed.")
