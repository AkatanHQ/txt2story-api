import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.analyze_image import AnalyzeImage  # Ensure this path is correct

# Initialize the AnalyzeImage class
analyzer = AnalyzeImage(provider="openai", vision_model="gpt-4o")

# Provide an image URL for testing
image_url = "https://vancouvergold.ca/wp-content/uploads/2013/11/person2-500x500.jpg"  # Replace with a real image URL

try:
    print("\n=== Testing Image Analysis via URL ===")
    result = analyzer.analyze_image_url(image_url)
    print(result)
except Exception as e:
    print(f"Error analyzing image from URL: {e}")

# Provide a local image file for testing
image_path = "tests/test_images/person1.webp"

try:
    print("\n=== Testing Image Analysis via File ===")
    result = analyzer.analyze_image_file(image_path)
    print(result)
except Exception as e:
    print(f"Error analyzing local image: {e}")
