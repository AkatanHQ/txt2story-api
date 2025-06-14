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
        "image_prompt": "Roger is sitting in the sun.",
        "entities": [
            {
                "name": "Roger",
                "appearance": "A man with a red hat.",
                "dreambooth_url": "https://storage.googleapis.com/aitoddlerstories/14/293/14_293_0_ad49547c-4455-48eb-a8b8-94732b9dc040.jpeg?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=aitoddlerstories-private%40aitoddlerstories.iam.gserviceaccount.com%2F20250427%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20250427T205016Z&X-Goog-Expires=86400&X-Goog-SignedHeaders=host&X-Goog-Signature=794f48789abe849744b4aa57aa2ec9c627f886d9387225200647b502e73eb3dabab8f4984943b7f00834bbd54214083665fa898b510b4acff96c316b77348ec8be7f83e5f3de9c63498aabcf714f88b95bae54c112243d781bd0635a0108cef79788037246f85461809fac871fc0fd95580ae3fb71a31855632c482592ba4611d41d105559a1e58c26ceafd498116016ce8e6f787ffe97c1200bab285a4af0442a8df51a6682127efbdc3fed46733a512725c0aefe941ca1f9ad75c56248b92112d191b109956dc898c64bd9ad08d388d94c43562df9bb9b4e4f6e91a2dd57444965cab5a0a090aacaa59441fc2e30d732576d617ad0650519786dd820cab2a3"
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
