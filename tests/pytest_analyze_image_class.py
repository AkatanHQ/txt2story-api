import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import base64
import pytest
from app.services.analyze_image import AnalyzeImage

@pytest.fixture
def analyzer():
    """
    Provides an instance of the AnalyzeImage class.
    """
    return AnalyzeImage(provider="openai", vision_model="gpt-4o")

def test_analyze_image_file(analyzer):
    """
    Test analyzing an image from a local file.
    """
    image_path = "tests/test_images/person1.webp"  # Update this with a real image path

    if not os.path.exists(image_path):
        pytest.skip("Test image file does not exist.")

    try:
        result = analyzer.analyze_image_file(image_path)
        assert isinstance(result, str) and len(result) > 0
        print("Test Passed: Image analysis returned a description.")
    except Exception as e:
        pytest.fail(f"Test Failed: {e}")

def test_analyze_image_bytes(analyzer):
    """
    Test analyzing an image provided as raw bytes.
    """
    image_path = "tests/test_images/person1.webp"  # Update this with a real image path

    if not os.path.exists(image_path):
        pytest.skip("Test image file does not exist.")

    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()

    try:
        result = analyzer.analyze_image_bytes(image_bytes)
        assert isinstance(result, str) and len(result) > 0
        print("Test Passed: Image analysis from bytes returned a description.")
    except Exception as e:
        pytest.fail(f"Test Failed: {e}")
